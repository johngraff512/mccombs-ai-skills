#!/usr/bin/env node
/**
 * McCombs Case Refresher — Refresh Memo .docx generation script
 *
 * Usage:
 *   node generate_refresh_memo_docx.js <input.json> <output.docx>
 *
 * For full case edition updates (Mode A), use the Case Generator's
 * generate_case_docx.js with an updated JSON file instead.
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
  console.error("Usage: node generate_refresh_memo_docx.js <input.json> <output.docx>");
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
const GREEN = "2E7D32";
const AMBER = "F57F17";
const RED = "C62828";
const SKILL_DIR = path.resolve(__dirname, "..");
const logoPath = path.join(SKILL_DIR, "assets", "mccombs_logo.png");
const logoData = fs.readFileSync(logoPath);

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------
const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

function makeHeaderCell(text, width) {
  return new TableCell({
    shading: { fill: BURNT_ORANGE, type: ShadingType.CLEAR },
    borders, width: { size: width, type: WidthType.DXA }, margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: WHITE, font: "Arial", size: 20 })] })]
  });
}

function makeDataCell(text, width, shaded, bold) {
  return new TableCell({
    shading: shaded ? { fill: LIGHT_GRAY, type: ShadingType.CLEAR } : undefined,
    borders, width: { size: width, type: WidthType.DXA }, margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text: String(text || ""), font: "Arial", size: 20, color: CHARCOAL, bold: !!bold })] })]
  });
}

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

function numbered(text, isLast = false) {
  return new Paragraph({
    spacing: { after: isLast ? 160 : 80 },
    numbering: { reference: "numbers", level: 0 },
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

function impactColor(impact) {
  const level = (impact || "").toLowerCase();
  if (level === "high") return RED;
  if (level === "medium") return AMBER;
  return GREEN;
}

function buildTable(headers, rows, boldFirstCol = false) {
  const TABLE_WIDTH = 9936;
  const numCols = headers.length;
  const colWidth = Math.floor(TABLE_WIDTH / numCols);
  const firstColWidth = TABLE_WIDTH - colWidth * (numCols - 1);
  const colWidths = [firstColWidth, ...Array(numCols - 1).fill(colWidth)];

  const headerRow = new TableRow({
    children: headers.map((h, i) => makeHeaderCell(h, colWidths[i]))
  });
  const dataRows = rows.map((row, idx) => {
    const shaded = idx % 2 === 1;
    const cells = Array.isArray(row) ? row : row.cells || [];
    return new TableRow({
      children: cells.map((c, ci) => makeDataCell(c, colWidths[ci], shaded, ci === 0 && boldFirstCol))
    });
  });
  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows]
  });
}

// ---------------------------------------------------------------------------
// Build Document
// ---------------------------------------------------------------------------
function buildDoc() {
  const c = [];

  // Title block
  c.push(new Paragraph({
    spacing: { after: 40 },
    children: [new TextRun({ text: data.title || "Case Refresh Memo", font: "Arial", size: 52, bold: true, color: BURNT_ORANGE })]
  }));
  if (data.meta) {
    c.push(new Paragraph({
      spacing: { after: 80 },
      children: [new TextRun({ text: data.meta, font: "Arial", size: 20, color: "999999" })]
    }));
  }
  c.push(accentRule());

  // Case info block
  if (data.caseName) c.push(labelValue("Case", data.caseName));
  if (data.company) c.push(labelValue("Company", data.company));
  if (data.protagonist) c.push(labelValue("Protagonist", data.protagonist));
  if (data.caseDate) c.push(labelValue("Original Case Date", data.caseDate));
  if (data.refreshDate) c.push(labelValue("Refresh Date", data.refreshDate));
  c.push(spacer(100));

  // Summary / Executive Summary
  if (data.summary) {
    c.push(h1("Executive Summary"));
    data.summary.split(/\n\n+/).forEach(p => { if (p.trim()) c.push(bodyPara(p.trim())); });
  }

  // Dilemma Status
  if (data.dilemmaStatus) {
    c.push(h1("Dilemma Status"));
    const ds = data.dilemmaStatus;
    // Status badge as a styled label-value
    const statusColor = ds.status === "Live" ? GREEN : ds.status === "Resolved" ? RED : AMBER;
    c.push(new Paragraph({
      spacing: { after: 120, line: 360 },
      children: [
        new TextRun({ text: "Status: ", font: "Arial", size: 24, bold: true, color: CHARCOAL }),
        new TextRun({ text: ds.status, font: "Arial", size: 24, bold: true, color: statusColor }),
      ]
    }));
    if (ds.explanation) c.push(bodyPara(ds.explanation));
  }

  // Key Updates
  if (data.updates && data.updates.length > 0) {
    c.push(h1("Key Updates"));

    // Group by category
    const categories = {};
    data.updates.forEach(u => {
      const cat = u.category || "General";
      if (!categories[cat]) categories[cat] = [];
      categories[cat].push(u);
    });

    Object.entries(categories).forEach(([category, updates]) => {
      c.push(h2(category));

      updates.forEach((u, idx) => {
        // Headline with impact badge
        c.push(new Paragraph({
          spacing: { before: idx > 0 ? 200 : 80, after: 60 },
          children: [
            new TextRun({ text: `[${(u.impact || "Medium").toUpperCase()}] `, font: "Arial", size: 22, bold: true, color: impactColor(u.impact) }),
            new TextRun({ text: u.headline, font: "Arial", size: 22, bold: true, color: CHARCOAL }),
          ]
        }));

        // Detail
        if (u.detail) c.push(bodyPara(u.detail, 100));

        // Source
        if (u.source) {
          c.push(new Paragraph({
            spacing: { after: 60 },
            children: [
              new TextRun({ text: "Source: ", font: "Arial", size: 18, bold: true, color: "999999" }),
              new TextRun({ text: u.source, font: "Arial", size: 18, color: "999999", italics: true }),
            ]
          }));
        }

        // Case implication
        if (u.caseImplication) {
          c.push(new Paragraph({
            spacing: { after: 120 },
            children: [
              new TextRun({ text: "Case implication: ", font: "Arial", size: 20, bold: true, color: CHARCOAL }),
              new TextRun({ text: u.caseImplication, font: "Arial", size: 20, color: CHARCOAL, italics: true }),
            ]
          }));
        }
      });
    });
  }

  // Revised Exhibits
  if (data.revisedExhibits && data.revisedExhibits.length > 0) {
    c.push(h1("Updated Exhibits"));
    data.revisedExhibits.forEach(exhibit => {
      if (exhibit.title) c.push(h2(exhibit.title));
      if (exhibit.headers && exhibit.rows) {
        c.push(buildTable(exhibit.headers, exhibit.rows.map(r => Array.isArray(r) ? r : r.cells || []), true));
        c.push(spacer(200));
      }
    });
  }

  // Teaching Implications
  if (data.teachingImplications && data.teachingImplications.length > 0) {
    c.push(h1("Teaching Implications"));
    data.teachingImplications.forEach((ti, i) => {
      c.push(numbered(ti, i === data.teachingImplications.length - 1));
    });
  }

  // Sources
  if (data.sources && data.sources.length > 0) {
    c.push(h1("Sources"));
    data.sources.forEach((src, i) => {
      c.push(new Paragraph({
        spacing: { after: 60 },
        children: [
          new TextRun({ text: `${src.number || i + 1}. `, font: "Arial", size: 20, bold: true, color: CHARCOAL }),
          new TextRun({ text: src.citation, font: "Arial", size: 20, color: CHARCOAL }),
        ]
      }));
    });
  }

  // Build document with McCombs branding
  return new Document({
    numbering: {
      config: [
        { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
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
              new TextRun({ text: "McCombs School of Business  |  CASE REFRESH MEMO", font: "Arial", size: 16, color: "999999" }),
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
  console.log("Refresh memo created: " + outputPath);
}

main().catch(err => {
  console.error("Error generating document:", err);
  process.exit(1);
});
