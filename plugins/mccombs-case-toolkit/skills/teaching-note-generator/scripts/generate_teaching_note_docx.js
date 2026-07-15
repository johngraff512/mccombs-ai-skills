#!/usr/bin/env node
/**
 * McCombs Teaching Note Generator — Reusable .docx generation script
 *
 * Usage:
 *   node generate_teaching_note_docx.js <input.json> <output.docx>
 *
 * Input JSON schema:
 * {
 *   "title": "Teaching Note: Case Title",
 *   "meta": "MBA Strategic Management  |  February 2026  |  INSTRUCTOR COPY — NOT FOR DISTRIBUTION",
 *   "synopsis": "Paragraph 1 text\n\nParagraph 2 text",
 *
 *   "learningObjectives": [
 *     { "objective": "Evaluate how...", "context": "Students demonstrate this when..." }
 *   ],
 *
 *   "positioning": {
 *     "suggestedCourses": ["MBA Strategic Management"],
 *     "whereinCurriculum": "Best placed in weeks 3-5...",
 *     "prerequisiteTopics": ["Porter's Five Forces", "Resource-Based View"],
 *     "pairedReadings": ["Porter, 'What is Strategy?' HBR 1996"]
 *   },
 *
 *   "preClassQuestions": [
 *     "What is Nvidia's primary source of competitive advantage?",
 *     "Which strategic path would you recommend, and why?"
 *   ],
 *
 *   "teachingPlan": [
 *     { "minutes": "0–10", "phase": "Opening", "activity": "Cold call...", "goal": "Surface divergent views." }
 *   ],
 *
 *   "discussionQuestions": [
 *     {
 *       "question": "What is Nvidia's competitive advantage?",
 *       "timing": "Minutes 0–20",
 *       "purpose": "Opens the competitive analysis...",
 *       "teachingPoints": ["CUDA is the moat, not the GPU", "Switching costs are in developer workflows"],
 *       "anticipatedResponses": "Most students will cite GPU performance first...",
 *       "boardCapture": "Column 1: Sources of Advantage"
 *     }
 *   ],
 *
 *   "boardPlan": {
 *     "description": "Three-column layout built left-to-right as discussion progresses.",
 *     "columns": [
 *       { "header": "Sources of Advantage", "points": ["CUDA ecosystem", "One-year cadence"] },
 *       { "header": "Competitive Threats", "points": ["Hyperscaler silicon", "AMD ROCm"] },
 *       { "header": "Strategic Options", "points": ["Fortify moat", "Open platform", "Evolve beyond chips"] }
 *     ]
 *   },
 *
 *   "epilogue": "Optional text about what actually happened..."
 * }
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
  WidthType, ShadingType, LevelFormat, PageBreak, PageNumber,
  TabStopType, TabStopPosition
} = require("docx");

// ---------------------------------------------------------------------------
// Args
// ---------------------------------------------------------------------------
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error("Usage: node generate_teaching_note_docx.js <input.json> <output.docx>");
  process.exit(1);
}
const inputPath = args[0];
const outputPath = args[1];
const tnData = JSON.parse(fs.readFileSync(inputPath, "utf-8"));

// ---------------------------------------------------------------------------
// Brand constants
// ---------------------------------------------------------------------------
const BURNT_ORANGE  = "BF5700";
const CHARCOAL      = "333F48";
const LIGHT_GRAY    = "F5F4F2";
const MED_GRAY      = "E8E6E3";
const WHITE         = "FFFFFF";
const SKILL_DIR     = path.resolve(__dirname, "..");
const logoPath      = path.join(SKILL_DIR, "assets", "mccombs_logo.png");
const logoData      = fs.readFileSync(logoPath);

// ---------------------------------------------------------------------------
// Table helpers
// ---------------------------------------------------------------------------
const thinBorder    = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders       = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const noBorders     = { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } };
const cellMargins   = { top: 80, bottom: 80, left: 120, right: 120 };

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
    children: [new Paragraph({ children: [new TextRun({ text: String(text), font: "Arial", size: 20, color: CHARCOAL, bold: !!bold })] })]
  });
}

function makeDataCellMultiline(lines, width, shaded) {
  return new TableCell({
    shading: shaded ? { fill: LIGHT_GRAY, type: ShadingType.CLEAR } : undefined,
    borders,
    width: { size: width, type: WidthType.DXA },
    margins: cellMargins,
    children: lines.map((line, i) => new Paragraph({
      spacing: { after: i < lines.length - 1 ? 60 : 0 },
      children: [new TextRun({ text: line, font: "Arial", size: 20, color: CHARCOAL })]
    }))
  });
}

// ---------------------------------------------------------------------------
// Content helpers
// ---------------------------------------------------------------------------
function bodyPara(text, spacingAfter = 200) {
  return new Paragraph({
    spacing: { after: spacingAfter, line: 360 },
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

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, font: "Arial", size: 24, bold: true, color: BURNT_ORANGE })]
  });
}

function labelValuePara(label, value) {
  return new Paragraph({
    spacing: { after: 120, line: 360 },
    children: [
      new TextRun({ text: label + ": ", font: "Arial", size: 22, bold: true, color: CHARCOAL }),
      new TextRun({ text: value, font: "Arial", size: 22, color: CHARCOAL })
    ]
  });
}

function bulletPara(text, isLast = false) {
  return new Paragraph({
    spacing: { after: isLast ? 160 : 60 },
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun({ text, font: "Arial", size: 22, color: CHARCOAL })]
  });
}

function numberedPara(text, isLast = false) {
  return new Paragraph({
    spacing: { after: isLast ? 160 : 80 },
    numbering: { reference: "numbers", level: 0 },
    children: [new TextRun({ text, font: "Arial", size: 22, color: CHARCOAL })]
  });
}

function dividerRule() {
  return new Paragraph({
    spacing: { before: 200, after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: "DDDDDD", space: 1 } },
    children: []
  });
}

// ---------------------------------------------------------------------------
// Teaching Plan table
// ---------------------------------------------------------------------------
function buildTeachingPlanTable(plan) {
  const TABLE_WIDTH = 9936;
  const colWidths = [1200, 1600, 4536, 2600]; // Time | Phase | Activity | Goal
  const headers = ["Time", "Phase", "Activity", "Instructor Goal"];

  const headerRow = new TableRow({
    children: headers.map((h, i) => makeHeaderCell(h, colWidths[i]))
  });

  const dataRows = plan.map((row, idx) => {
    const shaded = idx % 2 === 1;
    return new TableRow({
      children: [
        makeDataCell(row.minutes, colWidths[0], shaded, true),
        makeDataCell(row.phase,   colWidths[1], shaded, true),
        makeDataCell(row.activity, colWidths[2], shaded, false),
        makeDataCell(row.goal,    colWidths[3], shaded, false),
      ]
    });
  });

  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows]
  });
}

// ---------------------------------------------------------------------------
// Board Plan table
// ---------------------------------------------------------------------------
function buildBoardPlanTable(boardPlan) {
  const TABLE_WIDTH = 9936;
  const numCols = boardPlan.columns.length;
  const colWidth = Math.floor(TABLE_WIDTH / numCols);
  const firstColWidth = TABLE_WIDTH - colWidth * (numCols - 1);
  const colWidths = [firstColWidth, ...Array(numCols - 1).fill(colWidth)];

  const headerRow = new TableRow({
    children: boardPlan.columns.map((col, i) => makeHeaderCell(col.header, colWidths[i]))
  });

  // Find max points length across columns
  const maxRows = Math.max(...boardPlan.columns.map(c => c.points.length));

  const dataRows = [];
  for (let r = 0; r < maxRows; r++) {
    const shaded = r % 2 === 1;
    dataRows.push(new TableRow({
      children: boardPlan.columns.map((col, i) =>
        makeDataCell(col.points[r] || "", colWidths[i], shaded, false)
      )
    }));
  }

  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows]
  });
}

// ---------------------------------------------------------------------------
// Discussion question block
// ---------------------------------------------------------------------------
function buildDiscussionQuestion(dq, index) {
  const blocks = [];

  // Question header
  blocks.push(new Paragraph({
    spacing: { before: 300, after: 100 },
    children: [
      new TextRun({ text: `Q${index + 1}  `, font: "Arial", size: 26, bold: true, color: BURNT_ORANGE }),
      new TextRun({ text: dq.question, font: "Arial", size: 26, bold: true, color: CHARCOAL })
    ]
  }));

  // Timing badge
  blocks.push(new Paragraph({
    spacing: { after: 120 },
    children: [
      new TextRun({ text: "\u23F1  " + dq.timing, font: "Arial", size: 20, color: "888888", italics: true })
    ]
  }));

  // Purpose
  blocks.push(new Paragraph({
    spacing: { after: 80 },
    children: [
      new TextRun({ text: "Purpose: ", font: "Arial", size: 22, bold: true, color: CHARCOAL }),
      new TextRun({ text: dq.purpose, font: "Arial", size: 22, color: CHARCOAL })
    ]
  }));

  // Key Teaching Points
  if (dq.teachingPoints && dq.teachingPoints.length > 0) {
    blocks.push(new Paragraph({
      spacing: { before: 100, after: 60 },
      children: [new TextRun({ text: "Key Teaching Points", font: "Arial", size: 22, bold: true, color: CHARCOAL })]
    }));
    dq.teachingPoints.forEach((pt, i) => {
      blocks.push(bulletPara(pt, i === dq.teachingPoints.length - 1));
    });
  }

  // Anticipated Student Responses
  if (dq.anticipatedResponses) {
    blocks.push(new Paragraph({
      spacing: { before: 100, after: 60 },
      children: [new TextRun({ text: "Anticipated Student Responses: ", font: "Arial", size: 22, bold: true, color: CHARCOAL }),
                 new TextRun({ text: dq.anticipatedResponses, font: "Arial", size: 22, color: CHARCOAL })]
    }));
  }

  // Board Capture
  if (dq.boardCapture) {
    blocks.push(new Paragraph({
      spacing: { before: 80, after: 200 },
      children: [
        new TextRun({ text: "\uD83D\uDCCB  Board: ", font: "Arial", size: 20, bold: true, color: BURNT_ORANGE }),
        new TextRun({ text: dq.boardCapture, font: "Arial", size: 20, color: CHARCOAL, italics: true })
      ]
    }));
  }

  blocks.push(dividerRule());
  return blocks;
}

// ---------------------------------------------------------------------------
// Assemble document children
// ---------------------------------------------------------------------------
const children = [];

// ── Title block ─────────────────────────────────────────────────────────────
children.push(new Paragraph({
  spacing: { after: 80 },
  children: [new TextRun({ text: tnData.title, font: "Arial", size: 52, bold: true, color: BURNT_ORANGE })]
}));

if (tnData.meta) {
  children.push(new Paragraph({
    spacing: { after: 160 },
    children: [new TextRun({ text: tnData.meta, font: "Arial", size: 20, color: "999999" })]
  }));
}

// Burnt Orange accent rule
children.push(new Paragraph({
  spacing: { before: 60, after: 240 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BURNT_ORANGE, space: 1 } },
  children: []
}));

// ── Synopsis ─────────────────────────────────────────────────────────────────
children.push(h1("Synopsis"));
if (tnData.synopsis) {
  tnData.synopsis.split(/\n\n+/).forEach(para => {
    if (para.trim()) children.push(bodyPara(para.trim()));
  });
}

// ── Learning Objectives ──────────────────────────────────────────────────────
children.push(h1("Learning Objectives"));
if (tnData.learningObjectives && tnData.learningObjectives.length > 0) {
  tnData.learningObjectives.forEach((lo, i) => {
    // Objective number + text
    children.push(new Paragraph({
      spacing: { before: i === 0 ? 0 : 160, after: 60 },
      children: [
        new TextRun({ text: `${i + 1}.  `, font: "Arial", size: 22, bold: true, color: BURNT_ORANGE }),
        new TextRun({ text: lo.objective, font: "Arial", size: 22, bold: true, color: CHARCOAL })
      ]
    }));
    // Context line
    if (lo.context) {
      children.push(new Paragraph({
        spacing: { after: 80 },
        indent: { left: 360 },
        children: [
          new TextRun({ text: "What it looks like: ", font: "Arial", size: 21, italics: true, color: "666666" }),
          new TextRun({ text: lo.context, font: "Arial", size: 21, italics: true, color: "666666" })
        ]
      }));
    }
  });
}

// ── Positioning ──────────────────────────────────────────────────────────────
children.push(h1("Suggested Positioning"));
if (tnData.positioning) {
  const p = tnData.positioning;

  if (p.suggestedCourses && p.suggestedCourses.length > 0) {
    children.push(new Paragraph({
      spacing: { after: 60 },
      children: [new TextRun({ text: "Suggested Courses", font: "Arial", size: 22, bold: true, color: CHARCOAL })]
    }));
    p.suggestedCourses.forEach((c, i) => children.push(bulletPara(c, i === p.suggestedCourses.length - 1)));
  }

  if (p.whereinCurriculum) {
    children.push(labelValuePara("Where in Curriculum", p.whereinCurriculum));
  }

  if (p.prerequisiteTopics && p.prerequisiteTopics.length > 0) {
    children.push(new Paragraph({
      spacing: { before: 120, after: 60 },
      children: [new TextRun({ text: "Prerequisite Topics", font: "Arial", size: 22, bold: true, color: CHARCOAL })]
    }));
    p.prerequisiteTopics.forEach((t, i) => children.push(bulletPara(t, i === p.prerequisiteTopics.length - 1)));
  }

  if (p.pairedReadings && p.pairedReadings.length > 0) {
    children.push(new Paragraph({
      spacing: { before: 120, after: 60 },
      children: [new TextRun({ text: "Paired Readings", font: "Arial", size: 22, bold: true, color: CHARCOAL })]
    }));
    p.pairedReadings.forEach((r, i) => children.push(bulletPara(r, i === p.pairedReadings.length - 1)));
  }
}

// ── Pre-Class Assignment Questions ───────────────────────────────────────────
children.push(h1("Pre-Class Assignment Questions"));
children.push(bodyPara("Distribute to students before class. Students should come prepared to defend a position on Q2.", 120));
if (tnData.preClassQuestions && tnData.preClassQuestions.length > 0) {
  tnData.preClassQuestions.forEach((q, i) => children.push(numberedPara(q, i === tnData.preClassQuestions.length - 1)));
}

// ── Teaching Plan ─────────────────────────────────────────────────────────────
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("Teaching Plan"));
if (tnData.teachingPlan && tnData.teachingPlan.length > 0) {
  children.push(buildTeachingPlanTable(tnData.teachingPlan));
  children.push(new Paragraph({ spacing: { after: 200 }, children: [] }));
}

// ── Discussion Questions ──────────────────────────────────────────────────────
children.push(h1("Discussion Questions + Analysis"));
if (tnData.discussionQuestions && tnData.discussionQuestions.length > 0) {
  tnData.discussionQuestions.forEach((dq, i) => {
    children.push(...buildDiscussionQuestion(dq, i));
  });
}

// ── Board Plan ────────────────────────────────────────────────────────────────
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("Board Plan"));
if (tnData.boardPlan) {
  if (tnData.boardPlan.description) {
    children.push(bodyPara(tnData.boardPlan.description, 160));
  }
  if (tnData.boardPlan.columns && tnData.boardPlan.columns.length > 0) {
    children.push(buildBoardPlanTable(tnData.boardPlan));
    children.push(new Paragraph({ spacing: { after: 200 }, children: [] }));
  }
}

// ── Epilogue (optional) ───────────────────────────────────────────────────────
if (tnData.epilogue) {
  children.push(h1("Epilogue"));
  children.push(new Paragraph({
    spacing: { after: 100 },
    children: [new TextRun({
      text: "For instructor use only. Reveal at the instructor's discretion, typically after students have defended their recommendations.",
      font: "Arial", size: 20, italics: true, color: "888888"
    })]
  }));
  tnData.epilogue.split(/\n\n+/).forEach(para => {
    if (para.trim()) children.push(bodyPara(para.trim()));
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
  styles: {
    default: {
      document: { run: { font: "Arial", size: 24, color: CHARCOAL } }
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 32, bold: true, color: BURNT_ORANGE },
        paragraph: { spacing: { before: 400, after: 140 }, keepNext: true, keepLines: true, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 26, color: BURNT_ORANGE, allCaps: true },
        paragraph: { spacing: { before: 320, after: 100 }, keepNext: true, keepLines: true, outlineLevel: 1 }
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 24, bold: true, color: BURNT_ORANGE },
        paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, keepLines: true, outlineLevel: 2 }
      }
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
        children: [new Paragraph({
          children: [new ImageRun({
            type: "png",
            data: logoData,
            transformation: { width: 216, height: 27 },
            altText: { title: "McCombs School of Business", description: "McCombs School of Business logo", name: "McCombs Logo" }
          })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          tabStops: [{ type: TabStopType.RIGHT, position: 9936 }],
          children: [
            new TextRun({ text: "McCombs School of Business  |  The University of Texas at Austin  |  INSTRUCTOR COPY", font: "Arial", size: 16, color: "999999" }),
            new TextRun({ text: "\t", font: "Arial", size: 16 }),
            new TextRun({ text: "Page ", font: "Arial", size: 16, color: "999999" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "999999" }),
          ]
        })]
      })
    },
    children
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outputPath, buffer);
  console.log("Teaching note created: " + outputPath);
}).catch(err => {
  console.error("Error generating document:", err);
  process.exit(1);
});
