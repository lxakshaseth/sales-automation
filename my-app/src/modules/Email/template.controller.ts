import { NextRequest, NextResponse } from "next/server";
import Template from "./template.model";
import mongoose from "mongoose";
import { createAuditLog } from "../audit-log/auditLog.service";

type Params = {
  params: Promise<{ id: string }>;
};

export const createTemplateController = async (
  req: NextRequest,
) => {
  try {
    const body = await req.json();

    const template = await Template.create(body);

    await createAuditLog(
      "Templates",
      "Create",
      template.name,
      "Template created"
    );

    return NextResponse.json(
      {
        success: true,
        data: template,
      },
      {
        status: 201,
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

export const getTemplatesController = async () => {
  try {
    const templates = await Template.find().sort({
      createdAt: -1,
    });

    return NextResponse.json(
      {
        success: true,
        data: templates,
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

export const getTemplateByIdController = async (
  req: NextRequest,
  context: Params,
) => {
  try {
    const { id } = await context.params;

    if (!mongoose.Types.ObjectId.isValid(id)) {
      return NextResponse.json(
        {
          success: false,
          message: "Invalid template id",
        },
        {
          status: 400,
        },
      );
    }

    const template = await Template.findById(id);

    if (!template) {
      return NextResponse.json(
        {
          success: false,
          message: "Template not found",
        },
        {
          status: 404,
        },
      );
    }

    return NextResponse.json(
      {
        success: true,
        data: template,
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

export const updateTemplateController = async (
  req: NextRequest,
  context: Params,
) => {
  try {
    const { id } = await context.params;

    const body = await req.json();

    const oldTemplate = await Template.findById(id);

    const template =
      await Template.findByIdAndUpdate(
        id,
        body,
        {
          new: true,
        },
      );

    if (!template) {
      return NextResponse.json(
        {
          success: false,
          message: "Template not found",
        },
        {
          status: 404,
        },
      );
    }

    let details = "Template updated";

      if (
        body.name &&
        oldTemplate?.name !== body.name
      ) {
        details = "Template name changed";
      }
      else if (
        body.subject &&
        oldTemplate?.subject !== body.subject
      ) {
        details = "Subject updated";
      }
      else if (
        body.body &&
        oldTemplate?.body !== body.body
      ) {
        details = "Template content updated";
      }
      else if (
        body.type &&
        oldTemplate?.type !== body.type
      ) {
        details = "Template type changed";
      }

      await createAuditLog(
        "Templates",
        "Update",
        template.name,
        details
      );

    return NextResponse.json(
      {
        success: true,
        data: template,
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

export const deleteTemplateController = async (
  req: NextRequest,
  context: Params,
) => {
  try {
    const { id } = await context.params;

    const template =
      await Template.findByIdAndDelete(id);

      await createAuditLog(
        "Templates",
        "Delete",
        template?.name,
        "Template removed"
      );

    if (!template) {
      return NextResponse.json(
        {
          success: false,
          message: "Template not found",
        },
        {
          status: 404,
        },
      );
    }

    return NextResponse.json(
      {
        success: true,
        message: "Template deleted",
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