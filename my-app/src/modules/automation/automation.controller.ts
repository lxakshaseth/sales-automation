import { NextRequest, NextResponse } from "next/server";

import { assignMultipleLeadsToCampaign } from "./assignMultipleLead.service";

import { assignSingleLead } from "./assignSingleLead.service";

export const assignSingleLeadController =
  async (req: NextRequest) => {
    try {
      const { leadId, campaignId } =
        await req.json();

      if (!leadId || !campaignId) {
        return NextResponse.json(
          {
            success: false,
            message: "leadId and campaignId are required",
          },
          {
            status: 400,
          },
        );
      }

      const lead =
        await assignSingleLead(
          leadId,
          campaignId,
        );

      return NextResponse.json(
        {
          success: true,
          data: lead,
        },
        {
          status: 200,
        },
      );
    } catch (error: any) {
      return NextResponse.json(
        {
          success: false,
          message: error.message,
        },
        {
          status: 500,
        },
      );
    }
  };

export const assignMultipleLeadsController =
  async (req: NextRequest) => {
    try {
      const { campaignId, leadIds } =
        await req.json();

      if (
        !campaignId ||
        !leadIds ||
        !Array.isArray(leadIds)
      ) {
        return NextResponse.json(
          {
            success: false,
            message: "Invalid request body",
          },
          {
            status: 400,
          },
        );
      }

      const leads =
        await assignMultipleLeadsToCampaign(
          leadIds,
          campaignId,
        );

      return NextResponse.json(
        {
          success: true,
          totalAssigned: leads.length,
          data: leads,
        },
        {
          status: 200,
        },
      );
    } catch (error: any) {
      return NextResponse.json(
        {
          success: false,
          message: error.message,
        },
        {
          status: 500,
        },
      );
    }
  };