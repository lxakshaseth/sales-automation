type ConversationSummaryContact = {
  customName?: string;
  name?: string;
  phone?: string;
  waId: string;
  closedAt?: Date | string;
};

type ConversationSummaryMessage = {
  direction: "INBOUND" | "OUTBOUND";
  message?: string;
  createdAt: Date | string;
};

type PdfColor = [number, number, number];

type TextOptions = {
  font?: "F1" | "F2";
  color?: PdfColor;
  maxLines?: number;
};

const PAGE_WIDTH = 595.28;
const PAGE_HEIGHT = 841.89;
const FOOTER_TOP = 803;
const CONTENT_BOTTOM = 780;

const COLORS = {
  navy: [0.02, 0.03, 0.18] as PdfColor,
  navy2: [0.06, 0.05, 0.42] as PdfColor,
  purple: [0.28, 0.17, 0.86] as PdfColor,
  blue: [0.08, 0.39, 0.92] as PdfColor,
  blueSoft: [0.92, 0.96, 1] as PdfColor,
  green: [0.08, 0.61, 0.35] as PdfColor,
  greenSoft: [0.91, 0.98, 0.94] as PdfColor,
  amber: [0.9, 0.54, 0.05] as PdfColor,
  amberSoft: [1, 0.96, 0.88] as PdfColor,
  lavender: [0.94, 0.91, 1] as PdfColor,
  slate: [0.09, 0.12, 0.22] as PdfColor,
  muted: [0.41, 0.46, 0.57] as PdfColor,
  line: [0.84, 0.88, 0.94] as PdfColor,
  white: [1, 1, 1] as PdfColor,
};

class PdfDocument {
  private pages: string[][] = [];
  private currentPage: string[] = [];

  addPage() {
    this.currentPage = [];
    this.pages.push(this.currentPage);
    return this.pages.length;
  }

  get pageNumber() {
    return this.pages.length;
  }

  drawText(
    text: string,
    x: number,
    y: number,
    size: number,
    options: TextOptions = {},
  ) {
    const font = options.font || "F1";
    const color = options.color || COLORS.slate;
    const baseline = PAGE_HEIGHT - y - size;

    this.op(
      `BT /${font} ${fmt(size)} Tf ${rgb(color)} rg ${fmt(x)} ${fmt(
        baseline,
      )} Td (${escapePdfText(cleanText(text))}) Tj ET`,
    );
  }

  drawWrappedText(
    text: string,
    x: number,
    y: number,
    maxWidth: number,
    size: number,
    options: TextOptions = {},
  ) {
    const lines = wrapText(cleanText(text), maxWidth, size, options.font);
    const maxLines = options.maxLines || lines.length;
    const visibleLines = lines.slice(0, maxLines);
    const lineHeight = size * 1.36;

    if (lines.length > maxLines && visibleLines.length) {
      visibleLines[visibleLines.length - 1] = truncateLine(
        visibleLines[visibleLines.length - 1],
        maxWidth,
        size,
        options.font,
      );
    }

    visibleLines.forEach((line, index) => {
      this.drawText(line, x, y + index * lineHeight, size, options);
    });

    return y + visibleLines.length * lineHeight;
  }

  roundedRect(
    x: number,
    y: number,
    width: number,
    height: number,
    radius: number,
    fill: PdfColor,
    stroke?: PdfColor,
  ) {
    const right = x + width;
    const bottom = y + height;
    const c = radius * 0.5522847498;
    const commands = [
      `${fmt(x + radius)} ${fmt(toPdfY(y))} m`,
      `${fmt(right - radius)} ${fmt(toPdfY(y))} l`,
      `${fmt(right - radius + c)} ${fmt(toPdfY(y))} ${fmt(right)} ${fmt(
        toPdfY(y + radius - c),
      )} ${fmt(right)} ${fmt(toPdfY(y + radius))} c`,
      `${fmt(right)} ${fmt(toPdfY(bottom - radius))} l`,
      `${fmt(right)} ${fmt(toPdfY(bottom - radius + c))} ${fmt(
        right - radius + c,
      )} ${fmt(toPdfY(bottom))} ${fmt(right - radius)} ${fmt(
        toPdfY(bottom),
      )} c`,
      `${fmt(x + radius)} ${fmt(toPdfY(bottom))} l`,
      `${fmt(x + radius - c)} ${fmt(toPdfY(bottom))} ${fmt(x)} ${fmt(
        toPdfY(bottom - radius + c),
      )} ${fmt(x)} ${fmt(toPdfY(bottom - radius))} c`,
      `${fmt(x)} ${fmt(toPdfY(y + radius))} l`,
      `${fmt(x)} ${fmt(toPdfY(y + radius - c))} ${fmt(x + radius - c)} ${fmt(
        toPdfY(y),
      )} ${fmt(x + radius)} ${fmt(toPdfY(y))} c`,
      "h",
    ];

    this.op(`${rgb(fill)} rg`);

    if (stroke) {
      this.op(`${rgb(stroke)} RG 0.8 w`);
      this.op(`${commands.join("\n")} B`);
      return;
    }

    this.op(`${commands.join("\n")} f`);
  }

  rect(x: number, y: number, width: number, height: number, fill: PdfColor) {
    this.op(
      `${rgb(fill)} rg ${fmt(x)} ${fmt(PAGE_HEIGHT - y - height)} ${fmt(
        width,
      )} ${fmt(height)} re f`,
    );
  }

  line(x1: number, y1: number, x2: number, y2: number, color: PdfColor) {
    this.op(
      `${rgb(color)} RG 0.8 w ${fmt(x1)} ${fmt(toPdfY(y1))} m ${fmt(
        x2,
      )} ${fmt(toPdfY(y2))} l S`,
    );
  }

  circle(x: number, y: number, radius: number, fill: PdfColor) {
    const c = radius * 0.5522847498;
    const cy = toPdfY(y);

    this.op(`${rgb(fill)} rg`);
    this.op(
      [
        `${fmt(x + radius)} ${fmt(cy)} m`,
        `${fmt(x + radius)} ${fmt(cy + c)} ${fmt(x + c)} ${fmt(
          cy + radius,
        )} ${fmt(x)} ${fmt(cy + radius)} c`,
        `${fmt(x - c)} ${fmt(cy + radius)} ${fmt(x - radius)} ${fmt(
          cy + c,
        )} ${fmt(x - radius)} ${fmt(cy)} c`,
        `${fmt(x - radius)} ${fmt(cy - c)} ${fmt(x - c)} ${fmt(
          cy - radius,
        )} ${fmt(x)} ${fmt(cy - radius)} c`,
        `${fmt(x + c)} ${fmt(cy - radius)} ${fmt(x + radius)} ${fmt(
          cy - c,
        )} ${fmt(x + radius)} ${fmt(cy)} c`,
        "h f",
      ].join("\n"),
    );
  }

  toBuffer() {
    const objects: string[] = [];

    objects.push("<< /Type /Catalog /Pages 2 0 R >>");

    const pageObjectIds = this.pages.map((_, index) => 5 + index * 2);
    objects.push(
      `<< /Type /Pages /Kids [${pageObjectIds
        .map((id) => `${id} 0 R`)
        .join(" ")}] /Count ${this.pages.length} >>`,
    );
    objects.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
    objects.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>");

    this.pages.forEach((page, index) => {
      const contentObjectId = pageObjectIds[index] + 1;
      const stream = page.join("\n");

      objects.push(
        `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${fmt(
          PAGE_WIDTH,
        )} ${fmt(
          PAGE_HEIGHT,
        )}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents ${contentObjectId} 0 R >>`,
      );
      objects.push(
        `<< /Length ${Buffer.byteLength(stream, "latin1")} >>\nstream\n${stream}\nendstream`,
      );
    });

    return buildPdf(objects);
  }

  private op(command: string) {
    this.currentPage.push(command);
  }
}

export function buildConversationSummaryPdf({
  contact,
  messages,
  brandName = "YourBrand",
}: {
  contact: ConversationSummaryContact;
  messages: ConversationSummaryMessage[];
  brandName?: string;
}) {
  const summary = prepareSummary(contact, messages);
  const pdf = new PdfDocument();

  pdf.addPage();
  drawFooter(pdf, brandName);
  drawHero(pdf, summary);
  drawDetails(pdf, summary);

  let y = drawTranscriptHeader(pdf, 318);

  for (const message of summary.messages) {
    const rowHeight = measureMessageRow(message);

    if (y + rowHeight > CONTENT_BOTTOM) {
      pdf.addPage();
      drawFooter(pdf, brandName);
      y = drawContinuationHeader(pdf, summary);
    }

    y = drawMessageRow(pdf, message, y);
  }

  y += 14;

  if (y + 150 > CONTENT_BOTTOM) {
    pdf.addPage();
    drawFooter(pdf, brandName);
    y = drawContinuationHeader(pdf, summary);
  }

  drawBottomPanels(pdf, summary, y);

  return pdf.toBuffer();
}

function drawHero(pdf: PdfDocument, summary: ReturnType<typeof prepareSummary>) {
  pdf.drawText(`Subject: Conversation Summary - ${summary.contactName} (${summary.dateLabel})`, 24, 20, 8.5, {
    color: COLORS.slate,
  });
  pdf.drawText("View in browser", 508, 20, 8, {
    color: COLORS.slate,
  });

  pdf.roundedRect(24, 44, 547, 90, 9, COLORS.navy);
  pdf.roundedRect(24, 44, 547, 90, 9, COLORS.navy2);
  pdf.circle(58, 89, 18, COLORS.purple);
  pdf.drawText("CS", 48, 81, 11, {
    font: "F2",
    color: COLORS.white,
  });
  pdf.drawText("Conversation Summary", 92, 70, 22, {
    font: "F2",
    color: COLORS.white,
  });
  pdf.drawText("Detailed chat transcript with customer", 93, 100, 10, {
    color: [0.88, 0.91, 1],
  });
  pdf.roundedRect(453, 64, 96, 48, 8, [0.1, 0.09, 0.48]);
  pdf.drawText(summary.status, 476, 76, 8.5, {
    font: "F2",
    color: COLORS.white,
  });
  pdf.drawText(summary.closedAtLabel, 466, 96, 8, {
    color: [0.9, 0.93, 1],
  });
}

function drawDetails(pdf: PdfDocument, summary: ReturnType<typeof prepareSummary>) {
  pdf.roundedRect(24, 154, 547, 132, 8, COLORS.white, COLORS.line);

  pdf.drawText("CUSTOMER DETAILS", 58, 181, 10, {
    font: "F2",
    color: COLORS.navy2,
  });
  pdf.line(294, 178, 294, 264, COLORS.line);

  drawDetail(pdf, "Contact Name", summary.contactName, 58, 213);
  drawDetail(pdf, "Conversation Closed", summary.closedAtLabel, 190, 213);
  drawDetail(pdf, "Phone Number", summary.phone, 58, 254);
  drawDetail(pdf, "Status", summary.status, 190, 254);

  pdf.drawText("CONVERSATION OVERVIEW", 333, 181, 10, {
    font: "F2",
    color: COLORS.navy2,
  });

  drawStat(pdf, 315, 203, "CM", String(summary.customerMessages), "Customer", COLORS.blueSoft, COLORS.blue);
  drawStat(pdf, 375, 203, "BM", String(summary.businessMessages), "Business", COLORS.greenSoft, COLORS.green);
  drawStat(pdf, 435, 203, "TM", String(summary.totalMessages), "Total", COLORS.lavender, COLORS.purple);
  drawStat(pdf, 495, 203, "DU", summary.durationLabel, "Duration", COLORS.amberSoft, COLORS.amber);
}

function drawDetail(
  pdf: PdfDocument,
  label: string,
  value: string,
  x: number,
  y: number,
) {
  pdf.circle(x - 15, y + 3, 5, [0.94, 0.96, 1]);
  pdf.drawText(label, x, y, 7.5, {
    color: COLORS.muted,
  });
  pdf.drawWrappedText(value || "--", x, y + 14, 104, 8.2, {
    font: "F2",
    maxLines: 2,
  });
}

function drawStat(
  pdf: PdfDocument,
  x: number,
  y: number,
  icon: string,
  value: string,
  label: string,
  fill: PdfColor,
  accent: PdfColor,
) {
  pdf.roundedRect(x, y, 52, 61, 6, fill, COLORS.line);
  pdf.circle(x + 26, y + 18, 12, COLORS.white);
  pdf.drawText(icon, x + 18, y + 12, 7, {
    font: "F2",
    color: accent,
  });
  pdf.drawText(value, x + 14, y + 35, value.length > 4 ? 11 : 15, {
    font: "F2",
    color: COLORS.slate,
  });
  pdf.drawText(label, x + 12, y + 53, 6.5, {
    color: COLORS.slate,
  });
}

function drawTranscriptHeader(pdf: PdfDocument, y: number) {
  pdf.roundedRect(24, y - 18, 547, 38, 8, COLORS.white, COLORS.line);
  pdf.drawText("CHAT TRANSCRIPT", 58, y, 10, {
    font: "F2",
    color: COLORS.navy2,
  });
  pdf.roundedRect(172, y - 8, 70, 20, 10, COLORS.lavender);
  pdf.drawText("Timeline View", 189, y - 2, 6.5, {
    font: "F2",
    color: COLORS.purple,
  });
  pdf.drawText("Message View", 258, y - 2, 6.5, {
    color: COLORS.slate,
  });
  pdf.drawText("Summary View", 330, y - 2, 6.5, {
    color: COLORS.slate,
  });

  return y + 38;
}

function drawContinuationHeader(
  pdf: PdfDocument,
  summary: ReturnType<typeof prepareSummary>,
) {
  pdf.drawText(`Conversation Summary - ${summary.contactName}`, 24, 28, 12, {
    font: "F2",
    color: COLORS.navy2,
  });
  pdf.drawText(`Continued transcript | ${summary.dateLabel}`, 24, 46, 8, {
    color: COLORS.muted,
  });

  return drawTranscriptHeader(pdf, 82);
}

function drawMessageRow(
  pdf: PdfDocument,
  message: ReturnType<typeof prepareSummary>["messages"][number],
  y: number,
) {
  const isCustomer = message.direction === "INBOUND";
  const accent = isCustomer ? COLORS.blue : COLORS.green;
  const bubble = isCustomer ? COLORS.blueSoft : COLORS.greenSoft;
  const textWidth = 330;
  const wrapped = wrapText(message.text, textWidth - 20, 8.4);
  const lines = wrapped.slice(0, 8);
  const bubbleHeight = Math.max(24, lines.length * 11.4 + 14);
  const rowHeight = Math.max(34, bubbleHeight + 8);

  pdf.line(50, y - 7, 50, y + rowHeight - 3, COLORS.line);
  pdf.circle(50, y + 7, 3, accent);
  pdf.drawText(message.timeLabel, 62, y + 1, 7.2, {
    color: COLORS.slate,
  });
  pdf.circle(127, y + 7, 9, isCustomer ? [0.9, 0.95, 1] : [0.88, 0.98, 0.93]);
  pdf.drawText(isCustomer ? "C" : "B", 124, y + 1, 8, {
    font: "F2",
    color: accent,
  });
  pdf.drawText(isCustomer ? "Client" : "Business", 150, y + 2, 7.5, {
    font: "F2",
    color: accent,
  });
  pdf.roundedRect(205, y - 3, textWidth, bubbleHeight, 5, bubble, COLORS.line);

  lines.forEach((line, index) => {
    const visibleLine =
      wrapped.length > 8 && index === lines.length - 1
        ? truncateLine(line, textWidth - 20, 8.4)
        : line;

    pdf.drawText(visibleLine, 216, y + 6 + index * 11.4, 8.4, {
      color: COLORS.slate,
    });
  });

  return y + rowHeight;
}

function drawBottomPanels(
  pdf: PdfDocument,
  summary: ReturnType<typeof prepareSummary>,
  y: number,
) {
  pdf.roundedRect(24, y, 330, 62, 6, COLORS.white, COLORS.line);
  pdf.drawText("TOPICS DISCUSSED", 58, y + 20, 9, {
    font: "F2",
    color: COLORS.navy2,
  });

  let tagX = 42;
  let tagY = y + 35;

  for (const topic of summary.topics) {
    const tagWidth = Math.min(126, Math.max(46, estimateTextWidth(topic, 7.2) + 18));

    if (tagX + tagWidth > 340) {
      tagX = 42;
      tagY += 18;
    }

    pdf.roundedRect(tagX, tagY, tagWidth, 12, 6, [0.92, 0.95, 0.99]);
    pdf.drawText(topic, tagX + 8, tagY + 3, 6.8, {
      color: COLORS.slate,
    });
    tagX += tagWidth + 6;
  }

  pdf.roundedRect(366, y, 205, 62, 6, COLORS.white, COLORS.line);
  pdf.drawText("SENTIMENT ANALYSIS", 402, y + 20, 9, {
    font: "F2",
    color: COLORS.navy2,
  });
  pdf.drawText(summary.sentiment.label, 382, y + 40, 8, {
    font: "F2",
    color: summary.sentiment.label === "Needs Attention" ? COLORS.amber : COLORS.green,
  });
  pdf.roundedRect(382, y + 52, 145, 5, 3, [0.91, 0.94, 0.96]);
  pdf.roundedRect(
    382,
    y + 52,
    Math.max(16, 145 * (summary.sentiment.score / 100)),
    5,
    3,
    summary.sentiment.label === "Needs Attention" ? COLORS.amber : COLORS.green,
  );
  pdf.drawText(`${summary.sentiment.score}%`, 535, y + 48, 8, {
    font: "F2",
    color: COLORS.slate,
  });

  pdf.roundedRect(24, y + 76, 547, 46, 6, [0.95, 0.93, 1], [0.83, 0.78, 1]);
  pdf.circle(60, y + 99, 18, COLORS.purple);
  pdf.drawText("WA", 51, y + 91, 10, {
    font: "F2",
    color: COLORS.white,
  });
  pdf.drawText("Want to continue the conversation?", 92, y + 92, 11, {
    font: "F2",
    color: COLORS.navy2,
  });
  pdf.drawText("You can reply to this email or contact the customer directly.", 92, y + 110, 8, {
    color: COLORS.muted,
  });
  pdf.roundedRect(465, y + 87, 78, 24, 5, COLORS.purple);
  pdf.drawText("Reply to Customer", 476, y + 95, 7, {
    font: "F2",
    color: COLORS.white,
  });
}

function drawFooter(pdf: PdfDocument, brandName: string) {
  pdf.rect(0, FOOTER_TOP, PAGE_WIDTH, 39, COLORS.navy);
  pdf.drawText(brandName, 48, FOOTER_TOP + 16, 9, {
    font: "F2",
    color: COLORS.white,
  });
  pdf.drawText("This is an automated email. Please do not reply directly.", 190, FOOTER_TOP + 18, 7.5, {
    color: [0.88, 0.91, 1],
  });
  pdf.drawText(`Page ${pdf.pageNumber}`, 532, FOOTER_TOP + 18, 7.5, {
    color: [0.88, 0.91, 1],
  });
}

function measureMessageRow(
  message: ReturnType<typeof prepareSummary>["messages"][number],
) {
  const lines = wrapText(message.text, 310, 8.4).slice(0, 8);

  return Math.max(34, Math.max(24, lines.length * 11.4 + 14) + 8);
}

function prepareSummary(
  contact: ConversationSummaryContact,
  messages: ConversationSummaryMessage[],
) {
  const sortedMessages = [...messages].sort(
    (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
  );
  const closedAt = contact.closedAt
    ? new Date(contact.closedAt)
    : sortedMessages.length
      ? new Date(sortedMessages[sortedMessages.length - 1].createdAt)
      : new Date();
  const firstMessageAt = sortedMessages.length
    ? new Date(sortedMessages[0].createdAt)
    : closedAt;
  const customerMessages = sortedMessages.filter(
    (message) => message.direction === "INBOUND",
  ).length;
  const businessMessages = sortedMessages.filter(
    (message) => message.direction === "OUTBOUND",
  ).length;

  return {
    contactName: cleanText(getContactLabel(contact)),
    phone: cleanText(contact.phone || contact.waId || "--"),
    status: "Closed",
    closedAtLabel: formatDateTime(closedAt),
    dateLabel: formatDate(closedAt),
    customerMessages,
    businessMessages,
    totalMessages: sortedMessages.length,
    durationLabel: formatDuration(closedAt.getTime() - firstMessageAt.getTime()),
    topics: deriveTopics(sortedMessages),
    sentiment: deriveSentiment(sortedMessages),
    messages: sortedMessages.map((message) => ({
      direction: message.direction,
      text: cleanText(message.message || "(empty message)"),
      timeLabel: formatTime(new Date(message.createdAt)),
    })),
  };
}

function getContactLabel(contact: ConversationSummaryContact) {
  return contact.customName || contact.name || contact.phone || contact.waId;
}

function deriveTopics(messages: ConversationSummaryMessage[]) {
  const text = messages
    .map((message) => message.message || "")
    .join(" ")
    .toLowerCase();
  const topics: string[] = [];
  const topicRules: [string, RegExp][] = [
    ["Product Information", /\b(product|details|information|info|know)\b/],
    ["Pricing", /\b(price|pricing|cost|budget|quote|plan)\b/],
    ["Demo", /\b(demo|trial|walkthrough)\b/],
    ["Support", /\b(help|support|assist|issue|problem)\b/],
    ["Model Comparison", /\b(compare|comparison|best|recommend|option)\b/],
    ["Air Conditioners", /\b(ac|air conditioner|cool|portable|window|split)\b/],
    ["Antivirus Software", /\b(antivirus|virus|security|malware)\b/],
  ];

  for (const [topic, pattern] of topicRules) {
    if (pattern.test(text)) {
      topics.push(topic);
    }
  }

  if (!topics.length) {
    topics.push("General Inquiry");
  }

  return topics.slice(0, 8);
}

function deriveSentiment(messages: ConversationSummaryMessage[]) {
  const text = messages
    .map((message) => message.message || "")
    .join(" ")
    .toLowerCase();
  const positiveWords = ["thanks", "thank", "great", "nice", "good", "yes", "perfect", "helpful"];
  const negativeWords = ["angry", "bad", "issue", "problem", "not working", "wrong", "failed"];
  const positive = positiveWords.reduce(
    (count, word) => count + (text.includes(word) ? 1 : 0),
    0,
  );
  const negative = negativeWords.reduce(
    (count, word) => count + (text.includes(word) ? 1 : 0),
    0,
  );

  if (negative > positive) {
    return {
      label: "Needs Attention",
      score: Math.max(55, Math.min(88, 65 + negative * 6)),
    };
  }

  return {
    label: "Positive",
    score: Math.max(78, Math.min(96, 84 + positive * 3 - negative * 4)),
  };
}

function formatDate(date: Date) {
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });
}

function formatDateTime(date: Date) {
  return uppercaseMeridiem(
    date.toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
      timeZone: "Asia/Kolkata",
    }),
  );
}

function formatTime(date: Date) {
  return uppercaseMeridiem(
    date.toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
      timeZone: "Asia/Kolkata",
    }),
  );
}

function formatDuration(durationMs: number) {
  const totalMinutes = Math.max(1, Math.round(durationMs / 60000));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours > 0) {
    return `${hours}h ${String(minutes).padStart(2, "0")}m`;
  }

  return `${minutes}m`;
}

function wrapText(
  text: string,
  maxWidth: number,
  fontSize: number,
  font?: "F1" | "F2",
) {
  const words = text.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let line = "";

  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;

    if (estimateTextWidth(candidate, fontSize, font) <= maxWidth) {
      line = candidate;
      continue;
    }

    if (line) {
      lines.push(line);
    }

    if (estimateTextWidth(word, fontSize, font) > maxWidth) {
      const chunks = splitLongWord(word, maxWidth, fontSize, font);
      lines.push(...chunks.slice(0, -1));
      line = chunks[chunks.length - 1] || "";
    } else {
      line = word;
    }
  }

  if (line) {
    lines.push(line);
  }

  return lines.length ? lines : [""];
}

function splitLongWord(
  word: string,
  maxWidth: number,
  fontSize: number,
  font?: "F1" | "F2",
) {
  const chunks: string[] = [];
  let chunk = "";

  for (const char of word) {
    if (estimateTextWidth(chunk + char, fontSize, font) <= maxWidth) {
      chunk += char;
      continue;
    }

    if (chunk) {
      chunks.push(chunk);
    }

    chunk = char;
  }

  if (chunk) {
    chunks.push(chunk);
  }

  return chunks;
}

function truncateLine(
  line: string,
  maxWidth: number,
  fontSize: number,
  font?: "F1" | "F2",
) {
  let truncated = line;

  while (
    truncated.length > 0 &&
    estimateTextWidth(`${truncated}...`, fontSize, font) > maxWidth
  ) {
    truncated = truncated.slice(0, -1);
  }

  return `${truncated}...`;
}

function estimateTextWidth(text: string, fontSize: number, font?: "F1" | "F2") {
  const weight = font === "F2" ? 0.56 : 0.52;

  return text.length * fontSize * weight;
}

function cleanText(value: string) {
  return String(value)
    .replace(/[\u2010-\u2015]/g, "-")
    .replace(/\u00a0/g, " ")
    .normalize("NFKD")
    .replace(/[^\x20-\x7E]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function uppercaseMeridiem(value: string) {
  return value.replace(/\b(am|pm)\b/gi, (period) => period.toUpperCase());
}

function escapePdfText(value: string) {
  return value
    .replace(/\\/g, "\\\\")
    .replace(/\(/g, "\\(")
    .replace(/\)/g, "\\)");
}

function rgb(color: PdfColor) {
  return color.map(fmt).join(" ");
}

function fmt(value: number) {
  return Number(value.toFixed(2)).toString();
}

function toPdfY(y: number) {
  return PAGE_HEIGHT - y;
}

function buildPdf(objects: string[]) {
  const chunks: string[] = ["%PDF-1.4\n"];
  const offsets: number[] = [0];
  let offset = Buffer.byteLength(chunks[0], "latin1");

  objects.forEach((object, index) => {
    const chunk = `${index + 1} 0 obj\n${object}\nendobj\n`;

    offsets.push(offset);
    chunks.push(chunk);
    offset += Buffer.byteLength(chunk, "latin1");
  });

  const xrefOffset = offset;
  const xrefRows = offsets
    .map((objectOffset, index) => {
      if (index === 0) {
        return "0000000000 65535 f ";
      }

      return `${String(objectOffset).padStart(10, "0")} 00000 n `;
    })
    .join("\n");
  const trailer = `xref\n0 ${objects.length + 1}\n${xrefRows}\ntrailer\n<< /Size ${
    objects.length + 1
  } /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;

  chunks.push(trailer);

  return Buffer.from(chunks.join(""), "latin1");
}
