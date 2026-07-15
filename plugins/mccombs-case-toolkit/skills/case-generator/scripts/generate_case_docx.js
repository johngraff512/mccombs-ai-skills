#!/usr/bin/env node
/**
 * McCombs Case Generator — Reusable .docx generation script
 *
 * Usage:
 *   node generate_case_docx.js <input.json> <output.docx>
 *
 * Input JSON schema:
 * {
 *   "title": "Case Title",
 *   "subtitle": "Optional subtitle or tagline",
 *   "meta": "MBA Strategic Management  |  February 2026",
 *   "learningObjectives": [
 *     "Evaluate how Nvidia builds competitive advantage...",
 *     "Analyze Nvidia's platform ecosystem strategy..."
 *   ],
 *   "sections": [
 *     {
 *       "heading": "Section Title",          // H1 heading
 *       "content": [
 *         { "type": "paragraph", "text": "Body paragraph text..." },
 *         { "type": "paragraph", "runs": [
 *             { "text": "Bold lead-in. ", "bold": true },
 *             { "text": "Regular continuation text..." },
 *             { "type": "footnote_ref", "id": 1 }   // inline footnote reference
 *           ]
 *         },
 *         { "type": "subheading", "text": "Subsection Title" },  // H2
 *         { "type": "paragraph", "text": "More text..." }
 *       ]
 *     }
 *   ],
 *   "exhibits": [
 *     {
 *       "title": "Exhibit 1: Financial Summary",
 *       "headers": ["Metric", "FY2023", "FY2024", "FY2025"],
 *       "rows": [
 *         { "cells": ["Revenue ($B)", "$27.0", "$60.9", "$130.5"], "bold_first": true },
 *         { "cells": ["Gross Margin", "56.9%", "72.7%", "73.4%"], "bold_first": true }
 *       ],
 *       "source": "Sources: Nvidia Annual Reports; S&P Global Ratings."
 *     }
 *   ],
 *   "footnotes": {
 *     "1": "Full footnote text for reference 1. Include source citation here.",
 *     "2": "Full footnote text for reference 2."
 *   },
 *   "sources": [
 *     "Nvidia Corporation. Annual Report, Fiscal Year 2025.",
 *     "S&P Global Ratings. Revenue Forecast FY2026."
 *   ]
 * }
 *
 * Footnote guidance:
 *   Use footnotes for specific factual claims that can be verified — statistics,
 *   direct quotes, product announcements, financial figures, and any claim where
 *   a reader might reasonably want a citation. Place the footnote_ref run AFTER
 *   the relevant text, before any trailing punctuation if possible.
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
  WidthType, ShadingType, LevelFormat, PageBreak, PageNumber,
  TabStopType, TabStopPosition, FootnoteReferenceRun
} = require("docx");

// ---------------------------------------------------------------------------
// Args
// ---------------------------------------------------------------------------
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error("Usage: node generate_case_docx.js <input.json> <output.docx>");
  process.exit(1);
}
const inputPath = args[0];
const outputPath = args[1];

const caseData = JSON.parse(fs.readFileSync(inputPath, "utf-8"));

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
// Table helpers
// ---------------------------------------------------------------------------
const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

function makeHeaderCell(text, width) {
  return new TableCell({
    shading: { fill: BURNT_ORANGE, type: ShadingType.CLEAR },
    borders,
    width: { size: width, type: WidthType.DXA },
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: WHITE, font: "Arial", size: 20 })] })]
  });
}

function makeDataCell(text, width, shaded, bold) {
  return new TableCell({
    shading: shaded ? { fill: LIGHT_GRAY, type: ShadingType.CLEAR } : undefined,
    borders,
    width: { size: width, type: WidthType.DXA },
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, font: "Arial", size: 20, color: CHARCOAL, bold: !!bold })] })]
  });
}

// ---------------------------------------------------------------------------
// Content helpers
// ---------------------------------------------------------------------------
function bodyPara(text) {
  return new Paragraph({
    spacing: { after: 200, line: 360 },
    children: [new TextRun({ text, font: "Arial", size: 24, color: CHARCOAL })]
  });
}

function mixedPara(runs) {
  const children = runs.map(r => {
    // Footnote reference run — inserts a superscript reference number
    // Note: FootnoteReferenceRun takes a plain integer, NOT an options object
    if (r.type === "footnote_ref") {
      return new FootnoteReferenceRun(r.id);
    }
    // Regular text run (supports bold, italics, color, etc.)
    return new TextRun({ font: "Arial", size: 24, color: CHARCOAL, ...r });
  });
  return new Paragraph({ spacing: { after: 200, line: 360 }, children });
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

// ---------------------------------------------------------------------------
// Build content blocks from a section's content array
// ---------------------------------------------------------------------------
function buildContentBlocks(contentArray) {
  const blocks = [];
  for (const item of contentArray) {
    if (item.type === "paragraph" && item.text) {
      blocks.push(bodyPara(item.text));
    } else if (item.type === "paragraph" && item.runs) {
      blocks.push(mixedPara(item.runs));
    } else if (item.type === "subheading") {
      blocks.push(h2(item.text));
    }
  }
  return blocks;
}

// ---------------------------------------------------------------------------
// Build an exhibit table
// ---------------------------------------------------------------------------
function buildExhibit(exhibit) {
  const elements = [];
  elements.push(h2(exhibit.title));

  const numCols = exhibit.headers.length;
  const TABLE_WIDTH = 9936;
  const colWidth = Math.floor(TABLE_WIDTH / numCols);
  // Give first column extra space from rounding remainder
  const firstColWidth = TABLE_WIDTH - colWidth * (numCols - 1);
  const colWidths = [firstColWidth, ...Array(numCols - 1).fill(colWidth)];

  const headerRow = new TableRow({
    children: exhibit.headers.map((h, i) => makeHeaderCell(h, colWidths[i]))
  });

  const dataRows = exhibit.rows.map((row, rowIdx) => {
    const shaded = rowIdx % 2 === 1;
    return new TableRow({
      children: row.cells.map((cell, colIdx) =>
        makeDataCell(cell, colWidths[colIdx], shaded, colIdx === 0 && row.bold_first)
      )
    });
  });

  elements.push(new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows]
  }));

  if (exhibit.source) {
    elements.push(new Paragraph({
      spacing: { before: 80, after: 300 },
      children: [new TextRun({ text: exhibit.source, font: "Arial", size: 18, color: "888888", italics: true })]
    }));
  }

  return elements;
}

// ---------------------------------------------------------------------------
// Build footnotes map for Document constructor
// Expects caseData.footnotes = { "1": "footnote text", "2": "..." }
// ---------------------------------------------------------------------------
function buildFootnotes(footnotesData) {
  if (!footnotesData || Object.keys(footnotesData).length === 0) return undefined;
  const result = {};
  for (const [id, text] of Object.entries(footnotesData)) {
    result[parseInt(id, 10)] = {
      children: [new Paragraph({
        children: [new TextRun({ text, font: "Arial", size: 18, color: CHARCOAL })]
      })]
    };
  }
  return result;
}

// ---------------------------------------------------------------------------
// Assemble document children
// ---------------------------------------------------------------------------
const children = [];

// Title block
children.push(new Paragraph({
  spacing: { after: 100 },
  children: [new TextRun({ text: caseData.title, font: "Arial", size: 56, color: BURNT_ORANGE })]
}));

if (caseData.subtitle) {
  children.push(new Paragraph({
    spacing: { after: 80 },
    children: [new TextRun({ text: caseData.subtitle, font: "Arial", size: 28, color: CHARCOAL, italics: true })]
  }));
}

if (caseData.meta) {
  children.push(new Paragraph({
    spacing: { after: 200 },
    children: [new TextRun({ text: caseData.meta, font: "Arial", size: 22, color: "666666" })]
  }));
}

// Burnt Orange accent rule
children.push(new Paragraph({
  spacing: { before: 100, after: 200 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BURNT_ORANGE, space: 1 } },
  children: []
}));

// Learning objectives
if (caseData.learningObjectives && caseData.learningObjectives.length > 0) {
  children.push(new Paragraph({
    spacing: { before: 100, after: 80 },
    children: [new TextRun({ text: "Learning Objectives", font: "Arial", size: 24, bold: true, color: BURNT_ORANGE })]
  }));

  caseData.learningObjectives.forEach((lo, i) => {
    children.push(new Paragraph({
      spacing: { after: i === caseData.learningObjectives.length - 1 ? 200 : 60 },
      numbering: { reference: "bullets", level: 0 },
      children: [new TextRun({ text: lo, font: "Arial", size: 22, color: CHARCOAL })]
    }));
  });
}

// Case body sections
for (const section of caseData.sections) {
  children.push(h1(section.heading));
  children.push(...buildContentBlocks(section.content));
}

// Exhibits
if (caseData.exhibits && caseData.exhibits.length > 0) {
  children.push(new Paragraph({ children: [new PageBreak()] }));
  children.push(h1("Exhibits"));
  for (const exhibit of caseData.exhibits) {
    children.push(...buildExhibit(exhibit));
  }
}

// Sources
if (caseData.sources && caseData.sources.length > 0) {
  children.push(new Paragraph({ children: [new PageBreak()] }));
  children.push(h1("Sources"));
  caseData.sources.forEach(s => {
    children.push(new Paragraph({
      spacing: { after: 80 },
      numbering: { reference: "numbers", level: 0 },
      children: [new TextRun({ text: s, font: "Arial", size: 20, color: CHARCOAL })]
    }));
  });
}

// ---------------------------------------------------------------------------
// Build and write the document
// ---------------------------------------------------------------------------
const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
      {
        reference: "numbers",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
    ]
  },
  footnotes: buildFootnotes(caseData.footnotes),
  styles: {
    default: {
      document: {
        run: { font: "Arial", size: 24, color: CHARCOAL }
      }
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 32, bold: true, color: BURNT_ORANGE },
        paragraph: { spacing: { before: 360, after: 120 }, keepNext: true, keepLines: true, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 26, color: BURNT_ORANGE, allCaps: true },
        paragraph: { spacing: { before: 320, after: 100 }, keepNext: true, keepLines: true, outlineLevel: 1 }
      },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1152, bottom: 1152, left: 1152, header: 720, footer: 720 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            children: [
              new ImageRun({
                type: "png",
                data: logoData,
                transformation: { width: 216, height: 27 },
                altText: { title: "McCombs School of Business", description: "McCombs School of Business logo", name: "McCombs Logo" }
              })
            ]
          })
        ]
      })
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            tabStops: [{ type: TabStopType.RIGHT, position: 9936 }],
            children: [
              new TextRun({ text: "McCombs School of Business  |  The University of Texas at Austin", font: "Arial", size: 16, color: "999999" }),
              new TextRun({ text: "\t", font: "Arial", size: 16 }),
              new TextRun({ text: "Page ", font: "Arial", size: 16, color: "999999" }),
              new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "999999" }),
            ]
          })
        ]
      })
    },
    children
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outputPath, buffer);
  console.log("Document created: " + outputPath);
}).catch(err => {
  console.error("Error generating document:", err);
  process.exit(1);
});
