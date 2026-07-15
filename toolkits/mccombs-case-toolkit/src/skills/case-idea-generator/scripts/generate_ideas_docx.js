#!/usr/bin/env node
/**
 * McCombs Case Idea Generator — .docx generation script
 *
 * Usage:
 *   node generate_ideas_docx.js <input.json> <output.docx>
 *
 * See SKILL.md for the full JSON schema.
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
  WidthType, ShadingType, LevelFormat, PageNumber, TabStopType
} = require("docx");

// ---------------------------------------------------------------------------
// Args
// ---------------------------------------------------------------------------
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error("Usage: node generate_ideas_docx.js <input.json> <output.docx>");
  process.exit(1);
}
const inputPath = args[0];
const outputPath = args[1];
const data = JSON.parse(fs.readFileSync(inputPath, "utf-8"));

// ---------------------------------------------------------------------------
// Brand constants
// ---------------------------------------------------------------------------
const BURNT_ORANGE = "BF5700";
const CHARCOAL = "333F48";
const LIGHT_GRAY = "F5F4F2";
const WHITE = "FFFFFF";
const SKILL_DIR = path.resolve(__dirname, "..");
const logoPath = path.join(SKILL_DIR, "assets", "mccombs_logo.png");
const logoData = fs.readFileSync(logoPath);

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------
const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

function bodyPara(text, after = 200) {
  return new Paragraph({
    spacing: { after, line: 360 },
    children: [new TextRun({ text, font: "Arial", size: 24, color: CHARCOAL })]
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, font: "Arial", size: 32, bold: true, color: BURNT_ORANGE })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, font: "Arial", size: 26, color: BURNT_ORANGE, allCaps: true })]
  });
}

function bullet(text, isLast = false) {
  return new Paragraph({
    spacing: { after: isLast ? 160 : 60 },
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun({ text, font: "Arial", size: 22, color: CHARCOAL })]
  });
}

function labelValue(label, value) {
  return new Paragraph({
    spacing: { after: 120, line: 360 },
    children: [
      new TextRun({ text: label + ": ", font: "Arial", size: 22, bold: true, color: CHARCOAL }),
      new TextRun({ text: value, font: "Arial", size: 22, color: CHARCOAL })
    ]
  });
}

function accentRule() {
  return new Paragraph({
    spacing: { before: 60, after: 240 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BURNT_ORANGE, space: 1 } },
    children: []
  });
}

function spacer(after = 200) {
  return new Paragraph({ spacing: { after }, children: [] });
}

// ---------------------------------------------------------------------------
// Idea card builder — each idea gets a structured block
// ---------------------------------------------------------------------------
function buildIdeaCard(idea, index) {
  const blocks = [];

  // Idea number + company name as heading
  blocks.push(new Paragraph({
    spacing: { before: index > 0 ? 400 : 200, after: 80 },
    children: [
      new TextRun({ text: `Idea ${index + 1}: `, font: "Arial", size: 28, bold: true, color: BURNT_ORANGE }),
      new TextRun({ text: idea.company, font: "Arial", size: 28, bold: true, color: CHARCOAL })
    ]
  }));

  // Thin accent under the idea heading
  blocks.push(new Paragraph({
    spacing: { after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 3, color: BURNT_ORANGE, space: 1 } },
    children: []
  }));

  // Protagonist
  if (idea.protagonist) {
    blocks.push(labelValue("Protagonist", idea.protagonist));
  }

  // The Dilemma
  blocks.push(new Paragraph({
    spacing: { before: 160, after: 60 },
    children: [new TextRun({ text: "THE DILEMMA", font: "Arial", size: 20, bold: true, color: BURNT_ORANGE, allCaps: true })]
  }));
  blocks.push(bodyPara(idea.dilemma));

  // Why It's Teachable
  blocks.push(new Paragraph({
    spacing: { before: 160, after: 60 },
    children: [new TextRun({ text: "WHY IT'S TEACHABLE", font: "Arial", size: 20, bold: true, color: BURNT_ORANGE, allCaps: true })]
  }));
  blocks.push(bodyPara(idea.whyTeachable));

  // Key Frameworks
  if (idea.frameworks && idea.frameworks.length > 0) {
    blocks.push(new Paragraph({
      spacing: { before: 160, after: 60 },
      children: [new TextRun({ text: "KEY FRAMEWORKS", font: "Arial", size: 20, bold: true, color: BURNT_ORANGE, allCaps: true })]
    }));
    // Frameworks as inline comma-separated with tag-like styling
    blocks.push(new Paragraph({
      spacing: { after: 120 },
      children: [new TextRun({
        text: idea.frameworks.join("  |  "),
        font: "Arial", size: 22, color: CHARCOAL, italics: true
      })]
    }));
  }

  // Strategic Options
  if (idea.strategicOptions && idea.strategicOptions.length > 0) {
    blocks.push(new Paragraph({
      spacing: { before: 160, after: 60 },
      children: [new TextRun({ text: "STRATEGIC OPTIONS", font: "Arial", size: 20, bold: true, color: BURNT_ORANGE, allCaps: true })]
    }));
    idea.strategicOptions.forEach((opt, i) => {
      blocks.push(bullet(opt, i === idea.strategicOptions.length - 1));
    });
  }

  // Data Availability
  if (idea.dataAvailability) {
    blocks.push(new Paragraph({
      spacing: { before: 160, after: 60 },
      children: [new TextRun({ text: "DATA AVAILABILITY", font: "Arial", size: 20, bold: true, color: BURNT_ORANGE, allCaps: true })]
    }));
    blocks.push(bodyPara(idea.dataAvailability));
  }

  // Timeliness
  if (idea.timeliness) {
    blocks.push(labelValue("Timeliness", idea.timeliness));
  }

  // Source Leads
  if (idea.sourceleads && idea.sourceleads.length > 0) {
    blocks.push(new Paragraph({
      spacing: { before: 160, after: 60 },
      children: [new TextRun({ text: "SOURCE LEADS", font: "Arial", size: 20, bold: true, color: BURNT_ORANGE, allCaps: true })]
    }));
    idea.sourceleads.forEach((src, i) => {
      blocks.push(bullet(src, i === idea.sourceleads.length - 1));
    });
  }

  return blocks;
}

// ---------------------------------------------------------------------------
// Build Document
// ---------------------------------------------------------------------------
function buildDoc() {
  const c = [];

  // Title block
  c.push(new Paragraph({
    spacing: { after: 40 },
    children: [new TextRun({ text: data.title, font: "Arial", size: 52, bold: true, color: BURNT_ORANGE })]
  }));
  if (data.meta) {
    c.push(new Paragraph({
      spacing: { after: 80 },
      children: [new TextRun({ text: data.meta, font: "Arial", size: 20, color: "999999" })]
    }));
  }
  c.push(accentRule());

  // Context block
  if (data.context) {
    const ctx = data.context;
    if (ctx.topic) c.push(labelValue("Topic / Framework", ctx.topic));
    if (ctx.audience) c.push(labelValue("Target Audience", ctx.audience));
    if (ctx.requestedBy) c.push(labelValue("Requested By", ctx.requestedBy));
    if (ctx.generatedDate) c.push(labelValue("Generated", ctx.generatedDate));
    c.push(spacer(120));
  }

  // Ideas
  if (data.ideas && data.ideas.length > 0) {
    c.push(h1(`${data.ideas.length} Case Ideas`));
    data.ideas.forEach((idea, i) => {
      c.push(...buildIdeaCard(idea, i));
    });
  }

  // Selection Notes
  if (data.selectionNotes) {
    c.push(spacer(200));
    c.push(h1("Selection Notes"));
    data.selectionNotes.split(/\n\n+/).forEach(p => {
      if (p.trim()) c.push(bodyPara(p.trim()));
    });
  }

  // Build document with McCombs branding
  return new Document({
    numbering: {
      config: [
        { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      ]
    },
    styles: {
      default: { document: { run: { font: "Arial", size: 24, color: CHARCOAL } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: "Arial", size: 32, bold: true, color: BURNT_ORANGE }, paragraph: { spacing: { before: 400, after: 140 }, keepNext: true, keepLines: true, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: "Arial", size: 26, color: BURNT_ORANGE, allCaps: true }, paragraph: { spacing: { before: 320, after: 100 }, keepNext: true, keepLines: true, outlineLevel: 1 } },
      ]
    },
    sections: [{
      properties: {
        page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1152, bottom: 1152, left: 1152, header: 720, footer: 720 } }
      },
      headers: {
        default: new Header({ children: [new Paragraph({ children: [new ImageRun({ type: "png", data: logoData, transformation: { width: 216, height: 27 }, altText: { title: "McCombs School of Business", description: "McCombs School of Business logo", name: "McCombs Logo" } })] })] })
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            tabStops: [{ type: TabStopType.RIGHT, position: 9936 }],
            children: [
              new TextRun({ text: "McCombs School of Business  |  Case Ideas", font: "Arial", size: 16, color: "999999" }),
              new TextRun({ text: "\t", font: "Arial", size: 16 }),
              new TextRun({ text: "Page ", font: "Arial", size: 16, color: "999999" }),
              new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "999999" }),
            ]
          })]
        })
      },
      children: c
    }]
  });
}

// ---------------------------------------------------------------------------
// Generate
// ---------------------------------------------------------------------------
async function main() {
  const doc = buildDoc();
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log("Case ideas document created: " + outputPath);
}

main().catch(err => {
  console.error("Error generating document:", err);
  process.exit(1);
});
