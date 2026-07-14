import Lead from "./leads.model";
import { NextRequest, NextResponse } from "next/server";
import csv from "csv-parser";
import { Readable } from "stream";

const countryTimezoneMap: Record<string, any> = {
  india: "Asia/Kolkata",
  dubai: "Asia/Dubai",
  europe: "Europe/London",
};

export const bulkUploadLeadController = async (req: NextRequest) => {
  try {
    const formData = await req.formData();
    const file = formData.get("file") as File;

    if (!file) {
      return NextResponse.json(
        { success: false, message: "CSV file required" },
        { status: 400 },
      );
    }

    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    const results: any[] = [];

    await new Promise((resolve, reject) => {
      Readable.from(buffer)
        .pipe(csv())
        .on("data", (data) => {
          results.push(data);
        })
        .on("end", resolve)
        .on("error", reject);
    });

    // De-duplicate emails in the CSV
    const seenEmailsInCsv = new Set<string>();
    const uniqueRows: any[] = [];
    for (const row of results) {
      if (!row.email) continue;
      const emailLower = row.email.toLowerCase().trim();
      if (!emailLower) continue;
      if (seenEmailsInCsv.has(emailLower)) continue;
      seenEmailsInCsv.add(emailLower);
      uniqueRows.push(row);
    }

    const CHUNK_SIZE = 5000;
    let totalUploaded = 0;
    const insertedLeadsPreview: any[] = [];

    for (let i = 0; i < uniqueRows.length; i += CHUNK_SIZE) {
      const chunk = uniqueRows.slice(i, i + CHUNK_SIZE);
      const chunkEmails = chunk.map((row) => row.email.toLowerCase().trim());

      // Fetch existing leads in DB matching these emails
      const existingLeads = await Lead.find(
        { email: { $in: chunkEmails } },
        { email: 1 }
      ).lean();

      const existingEmails = new Set(
        existingLeads.map((lead) => lead.email.toLowerCase().trim())
      );

      const leadsToCreate = [];
      for (const row of chunk) {
        const emailLower = row.email.toLowerCase().trim();
        if (existingEmails.has(emailLower)) {
          continue;
        }

        const countryLower = row.country ? String(row.country).toLowerCase() : "";
        const stateLower = row.state ? String(row.state).toLowerCase() : "";
        const countryData = countryTimezoneMap[countryLower];

        const timezone =
          typeof countryData === "string"
            ? countryData
            : countryData?.[stateLower];

        leadsToCreate.push({
          firstName: row.firstName || "Unknown",
          lastName: row.lastName || "",
          email: row.email,
          phone: row.phone || "Unknown",
          company: row.company || "",
          country: row.country || "",
          state: row.state || "",
          timezone,
        });
      }

      if (leadsToCreate.length > 0) {
        try {
          const createdLeads = await Lead.insertMany(leadsToCreate, { ordered: false });
          totalUploaded += createdLeads.length;

          if (insertedLeadsPreview.length < 100) {
            insertedLeadsPreview.push(
              ...createdLeads.slice(0, 100 - insertedLeadsPreview.length)
            );
          }
        } catch (err: any) {
          // insertMany with ordered:false might insert some docs and throw an error for others (e.g. duplicate key or validation)
          if (err.name === "BulkWriteError" || err.name === "MongoBulkWriteError") {
            const insertedCount = err.result?.nInserted || 0;
            totalUploaded += insertedCount;
            const insertedDocs = err.insertedDocs || [];
            if (insertedLeadsPreview.length < 100 && insertedDocs.length > 0) {
              insertedLeadsPreview.push(
                ...insertedDocs.slice(0, 100 - insertedLeadsPreview.length)
              );
            }
            console.warn(`Bulk write warning: ${err.message}. Succeeded: ${insertedCount}`);
          } else {
            // Rethrow other errors (like validation errors that prevent any write)
            throw err;
          }
        }
      }
    }

    return NextResponse.json(
      {
        success: true,
        totalUploaded,
        data: insertedLeadsPreview,
      },
      { status: 201 },
    );
  } catch (error: any) {
    console.error("Bulk upload controller error:", error);
    return NextResponse.json(
      {
        success: false,
        message: error.message,
      },
      { status: 500 },
    );
  }
};
