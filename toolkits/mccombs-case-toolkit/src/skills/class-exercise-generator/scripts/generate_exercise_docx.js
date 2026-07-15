#!/usr/bin/env node
/**
 * McCombs Class Exercise Generator — .docx generation script (v2)
 *
 * Produces a SINGLE instructor exercise guide containing a menu of 5-8 exercises
 * for one class session. Each exercise is a self-contained "card" with all
 * facilitation details, student-facing content, and answer guidance.
 *
 * Usage:
 *   node generate_exercise_docx.js <input.json> <output.docx>
 *
 * JSON Schema:
 * {
 *   "title": "Class Exercises: Nvidia's AI Fortress",
 *   "meta": "MBA Strategic Management  |  February 2026",
 *   "caseName": "Nvidia's AI Fortress: Jensen Huang's Next Move",
 *   "sessionLength": 75,
 *   "classSize": 65,
 *   "learningObjectives": ["LO1", "LO2"],
 *   "menuSummary": "Overview of the exercise menu...",
 *   "exercises": [
 *     {
 *       "number": 1,
 *       "name": "Opening Poll: Where Do You Stand?",
 *       "type": "poll",             // poll, short_answer, think_pair_share, small_group, framework, debate, role_play, decision_memo, gallery_walk
 *       "phase": "Opening",         // Opening, Analysis, Synthesis, Close
 *       "essential": true,          // true = recommended, false = optional
 *       "duration": 3,
 *       "durationNotes": "Fixed — does not scale with class size",
 *       "purpose": "Activate prior thinking...",
 *       "prompt": "If you were Jensen Huang, which path...",
 *       "setup": "Display the poll question...",
 *       "facilitation": ["Note the vote distribution...", "Don't discuss yet..."],
 *       "debrief": "Use vote distribution to transition...",
 *       "studentContent": {         // null if none needed
 *         "type": "display",        // display (project on screen) or distribute (hand out)
 *         "title": "Analysis Framework",
 *         "content": "Text to display or print...",
 *         "table": {                // optional — for worksheets
 *           "headers": ["Element", "Your Analysis"],
 *           "rows": [["Question 1", ""], ["Question 2", ""]]
 *         }
 *       },
 *       "answerGuidance": {         // null if not needed
 *         "strongAnswers": ["Answer 1...", "Answer 2..."],
 *         "commonMisses": ["Students often overlook..."],
 *         "byGroup": [             // for group-specific guidance
 *           { "group": "Team 1", "strongArguments": "...", "weaknesses": "...", "expectedRating": "7" }
 *         ]
 *       }
 *     }
 *   ],
 *   "suggestedFlow": {
 *     "description": "Recommended sequence...",
 *     "sequence": [
 *       { "minutes": "0-3", "exercise": 1, "notes": "Opening poll" },
 *       { "minutes": "3-15", "exercise": null, "notes": "Instructor-led discussion" }
 *     ]
 *   }
 * }
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
  WidthType, ShadingType, LevelFormat, PageBreak, PageNumber,
  TabStopType
} = require("docx");

// ---------------------------------------------------------------------------
// Args
// ---------------------------------------------------------------------------
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error("Usage: node generate_exercise_docx.js <input.json> <output.docx>");
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
const STEEL_GRAY = "9CACB6";
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

function buildTable(headers, rows, boldFirstCol) {
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
    const cells = Array.isArray(row) ? row : (row.cells || row);
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
// Type labels and phase colors
// ---------------------------------------------------------------------------
const TYPE_LABELS = {
  poll: "Poll / Vote",
  short_answer: "Short Answer",
  think_pair_share: "Think-Pair-Share",
  small_group: "Small Group Breakout",
  framework: "Framework Application",
  debate: "Structured Debate",
  role_play: "Role Play",
  decision_memo: "Decision Memo",
  gallery_walk: "Gallery Walk"
};

function typeLabel(type) {
  return TYPE_LABELS[type] || type.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

// ---------------------------------------------------------------------------
// Exercise card builder
// ---------------------------------------------------------------------------
function buildExerciseCard(ex) {
  const blocks = [];

  // Exercise header: number + name
  // Use pageBreakBefore instead of standalone PageBreak to avoid blank pages
  blocks.push(new Paragraph({
    spacing: { after: 60 },
    pageBreakBefore: ex.number > 1,
    children: [
      new TextRun({ text: `Exercise ${ex.number}: `, font: "Arial", size: 30, bold: true, color: BURNT_ORANGE }),
      new TextRun({ text: ex.name, font: "Arial", size: 30, bold: true, color: CHARCOAL })
    ]
  }));

  // Accent line
  blocks.push(new Paragraph({
    spacing: { after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BURNT_ORANGE, space: 1 } },
    children: []
  }));

  // Metadata row: type | phase | duration | essential/optional
  const metaParts = [];
  if (ex.type) metaParts.push(typeLabel(ex.type));
  if (ex.phase) metaParts.push(ex.phase);
  if (ex.duration) metaParts.push(ex.duration + " min");
  metaParts.push(ex.essential !== false ? "Recommended" : "Optional");

  blocks.push(new Paragraph({
    spacing: { after: 160 },
    children: [new TextRun({
      text: metaParts.join("  \u2022  "),
      font: "Arial", size: 20, color: STEEL_GRAY, italics: true
    })]
  }));

  // Duration notes (if timing scales with class size)
  if (ex.durationNotes) {
    blocks.push(new Paragraph({
      spacing: { after: 120 },
      children: [
        new TextRun({ text: "\u23F1 Timing: ", font: "Arial", size: 20, bold: true, color: CHARCOAL }),
        new TextRun({ text: ex.durationNotes, font: "Arial", size: 20, color: CHARCOAL })
      ]
    }));
  }

  // Purpose
  if (ex.purpose) {
    blocks.push(new Paragraph({
      spacing: { before: 120, after: 60 },
      children: [new TextRun({ text: "PURPOSE", font: "Arial", size: 18, bold: true, color: BURNT_ORANGE })]
    }));
    blocks.push(bodyPara(ex.purpose, 160));
  }

  // Prompt — displayed prominently
  if (ex.prompt) {
    blocks.push(new Paragraph({
      spacing: { before: 120, after: 60 },
      children: [new TextRun({ text: "THE PROMPT", font: "Arial", size: 18, bold: true, color: BURNT_ORANGE })]
    }));
    // Prompt in a light-gray box effect (indented, slightly larger)
    blocks.push(new Paragraph({
      spacing: { after: 160 },
      indent: { left: 360, right: 360 },
      border: {
        left: { style: BorderStyle.SINGLE, size: 8, color: BURNT_ORANGE, space: 8 }
      },
      children: [new TextRun({
        text: ex.prompt,
        font: "Arial", size: 24, color: CHARCOAL, italics: true
      })]
    }));
  }

  // Setup
  if (ex.setup) {
    blocks.push(new Paragraph({
      spacing: { before: 120, after: 60 },
      children: [new TextRun({ text: "SETUP", font: "Arial", size: 18, bold: true, color: BURNT_ORANGE })]
    }));
    ex.setup.split(/\n\n+/).forEach(p => { if (p.trim()) blocks.push(bodyPara(p.trim(), 120)); });
  }

  // Facilitation notes
  if (ex.facilitation && ex.facilitation.length > 0) {
    blocks.push(new Paragraph({
      spacing: { before: 120, after: 60 },
      children: [new TextRun({ text: "FACILITATION NOTES", font: "Arial", size: 18, bold: true, color: BURNT_ORANGE })]
    }));
    ex.facilitation.forEach((n, i) => blocks.push(bullet(n, i === ex.facilitation.length - 1)));
  }

  // Debrief
  if (ex.debrief) {
    blocks.push(new Paragraph({
      spacing: { before: 120, after: 60 },
      children: [new TextRun({ text: "DEBRIEF / TRANSITION", font: "Arial", size: 18, bold: true, color: BURNT_ORANGE })]
    }));
    blocks.push(bodyPara(ex.debrief, 160));
  }

  // Student-facing content
  if (ex.studentContent) {
    const sc = ex.studentContent;
    const label = sc.type === "distribute" ? "STUDENT HANDOUT (Distribute)" : "DISPLAY FOR STUDENTS";
    blocks.push(new Paragraph({
      spacing: { before: 160, after: 60 },
      children: [new TextRun({ text: label, font: "Arial", size: 18, bold: true, color: BURNT_ORANGE })]
    }));

    if (sc.title) {
      blocks.push(new Paragraph({
        spacing: { after: 80 },
        children: [new TextRun({ text: sc.title, font: "Arial", size: 22, bold: true, color: CHARCOAL })]
      }));
    }

    if (sc.content) {
      sc.content.split(/\n/).forEach(line => {
        blocks.push(new Paragraph({
          spacing: { after: 60 },
          indent: { left: 360 },
          border: { left: { style: BorderStyle.SINGLE, size: 4, color: STEEL_GRAY, space: 8 } },
          children: [new TextRun({ text: line, font: "Arial", size: 22, color: CHARCOAL })]
        }));
      });
      blocks.push(spacer(80));
    }

    if (sc.table) {
      blocks.push(buildTable(
        sc.table.headers,
        sc.table.rows.map(r => Array.isArray(r) ? r : r.cells || [r]),
        true
      ));
      blocks.push(spacer(120));
    }
  }

  // Answer guidance
  if (ex.answerGuidance) {
    const ag = ex.answerGuidance;
    blocks.push(new Paragraph({
      spacing: { before: 160, after: 60 },
      children: [new TextRun({ text: "ANSWER GUIDANCE", font: "Arial", size: 18, bold: true, color: BURNT_ORANGE })]
    }));

    if (ag.strongAnswers && ag.strongAnswers.length > 0) {
      blocks.push(new Paragraph({
        spacing: { after: 40 },
        children: [new TextRun({ text: "Strong answers:", font: "Arial", size: 20, bold: true, color: CHARCOAL })]
      }));
      ag.strongAnswers.forEach((a, i) => blocks.push(bullet(a, i === ag.strongAnswers.length - 1)));
    }

    if (ag.commonMisses && ag.commonMisses.length > 0) {
      blocks.push(new Paragraph({
        spacing: { before: 80, after: 40 },
        children: [new TextRun({ text: "Common misses:", font: "Arial", size: 20, bold: true, color: CHARCOAL })]
      }));
      ag.commonMisses.forEach((m, i) => blocks.push(bullet(m, i === ag.commonMisses.length - 1)));
    }

    if (ag.byGroup && ag.byGroup.length > 0) {
      ag.byGroup.forEach(g => {
        blocks.push(new Paragraph({
          spacing: { before: 100, after: 40 },
          children: [new TextRun({ text: g.group, font: "Arial", size: 20, bold: true, color: CHARCOAL })]
        }));
        if (g.strongArguments) blocks.push(new Paragraph({
          spacing: { after: 40, line: 340 },
          children: [
            new TextRun({ text: "Strongest arguments: ", font: "Arial", size: 20, bold: true, color: CHARCOAL }),
            new TextRun({ text: g.strongArguments, font: "Arial", size: 20, color: CHARCOAL })
          ]
        }));
        if (g.weaknesses) blocks.push(new Paragraph({
          spacing: { after: 40, line: 340 },
          children: [
            new TextRun({ text: "Weaknesses: ", font: "Arial", size: 20, bold: true, color: CHARCOAL }),
            new TextRun({ text: g.weaknesses, font: "Arial", size: 20, color: CHARCOAL })
          ]
        }));
        if (g.expectedRating) blocks.push(new Paragraph({
          spacing: { after: 60, line: 340 },
          children: [
            new TextRun({ text: "Expected rating: ", font: "Arial", size: 20, bold: true, color: CHARCOAL }),
            new TextRun({ text: g.expectedRating, font: "Arial", size: 20, color: CHARCOAL })
          ]
        }));
      });
    }
  }

  return blocks;
}

// ---------------------------------------------------------------------------
// Build suggested flow table
// ---------------------------------------------------------------------------
function buildSuggestedFlow() {
  const blocks = [];
  const sf = data.suggestedFlow;
  if (!sf) return blocks;

  blocks.push(new Paragraph({ children: [new PageBreak()] }));
  blocks.push(h1("Suggested Session Flow"));
  if (sf.description) blocks.push(bodyPara(sf.description));

  const headers = ["Time", "Activity", "Notes"];
  const rows = sf.sequence.map(s => {
    const activity = s.exercise
      ? `Exercise ${s.exercise}`
      : "Instructor-Led";
    return [s.minutes, activity, s.notes || ""];
  });
  blocks.push(buildTable(headers, rows, true));

  return blocks;
}

// ---------------------------------------------------------------------------
// Build full document
// ---------------------------------------------------------------------------
function buildDoc() {
  const c = [];

  // Title block
  c.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: data.title || "Class Exercise Guide", font: "Arial", size: 52, bold: true, color: BURNT_ORANGE })] }));
  c.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "Instructor Exercise Guide", font: "Arial", size: 28, color: CHARCOAL, italics: true })] }));
  if (data.meta) c.push(new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: data.meta, font: "Arial", size: 20, color: "999999" })] }));
  c.push(accentRule());

  // Session info
  if (data.caseName) c.push(labelValue("Case", data.caseName));
  if (data.sessionLength) c.push(labelValue("Session Length", data.sessionLength + " minutes"));
  if (data.classSize) c.push(labelValue("Class Size", data.classSize + " students"));
  c.push(spacer(80));

  // Learning Objectives
  if (data.learningObjectives && data.learningObjectives.length > 0) {
    c.push(h1("Learning Objectives"));
    data.learningObjectives.forEach((lo, i) => c.push(bullet(lo, i === data.learningObjectives.length - 1)));
  }

  // Exercise Menu Summary
  if (data.menuSummary) {
    c.push(h1("Exercise Menu"));
    data.menuSummary.split(/\n\n+/).forEach(p => { if (p.trim()) c.push(bodyPara(p.trim())); });
  }

  // Quick reference table of all exercises
  if (data.exercises && data.exercises.length > 0) {
    c.push(spacer(80));
    const menuHeaders = ["#", "Exercise", "Type", "Phase", "Duration", "Status"];
    const menuRows = data.exercises.map(ex => [
      String(ex.number),
      ex.name,
      typeLabel(ex.type),
      ex.phase || "",
      (ex.duration || "?") + " min",
      ex.essential !== false ? "Recommended" : "Optional"
    ]);
    c.push(buildTable(menuHeaders, menuRows, true));
    c.push(spacer(200));
  }

  // Exercise cards
  if (data.exercises && data.exercises.length > 0) {
    data.exercises.forEach(ex => {
      c.push(...buildExerciseCard(ex));
    });
  }

  // Suggested flow
  c.push(...buildSuggestedFlow());

  // Build document
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
              new TextRun({ text: "McCombs School of Business  |  INSTRUCTOR EXERCISE GUIDE", font: "Arial", size: 16, color: "999999" }),
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
  console.log("Exercise guide created: " + outputPath);
}

main().catch(err => {
  console.error("Error generating document:", err);
  process.exit(1);
});
