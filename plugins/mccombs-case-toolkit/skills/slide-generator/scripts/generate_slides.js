#!/usr/bin/env node
/**
 * McCombs Slide Generator — .pptx generation script
 *
 * Usage:
 *   node generate_slides.js <input.json> <output.pptx>
 *
 * See SKILL.md for the full JSON schema and supported slide types.
 */

const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");

// ---------------------------------------------------------------------------
// Args
// ---------------------------------------------------------------------------
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error("Usage: node generate_slides.js <input.json> <output.pptx>");
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
const STEEL_GRAY = "9CACB6";
const WARM_GRAY = "D6D2C4";
const WHITE = "FFFFFF";
const LIGHT_BG = "F5F4F2";

const SKILL_DIR = path.resolve(__dirname, "..");
const logoColorPath = path.join(SKILL_DIR, "assets", "mccombs_logo_color.png");
const logoWhitePath = path.join(SKILL_DIR, "assets", "mccombs_logo_white.png");

// Logo dimensions (proportional to original 1799x226)
const LOGO_W = 2.5; // inches
const LOGO_H = LOGO_W * (226 / 1799);

// ---------------------------------------------------------------------------
// Create presentation
// ---------------------------------------------------------------------------
const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 inches
pptx.author = "McCombs Case Toolkit";
pptx.title = data.title || "McCombs Presentation";

// ---------------------------------------------------------------------------
// Helper: add logo to a slide
// ---------------------------------------------------------------------------
function addLogo(slide, variant = "color") {
  const logoPath = variant === "white" ? logoWhitePath : logoColorPath;
  slide.addImage({
    path: logoPath,
    x: 0.5,
    y: 7.5 - LOGO_H - 0.25,
    w: LOGO_W,
    h: LOGO_H,
  });
}

// ---------------------------------------------------------------------------
// Helper: add footnote text
// ---------------------------------------------------------------------------
function addFootnote(slide, text) {
  slide.addText(text, {
    x: 0.5, y: 6.9, w: 12.33, h: 0.3,
    fontSize: 9, fontFace: "Arial", color: "999999",
    align: "left", valign: "bottom"
  });
}

// ---------------------------------------------------------------------------
// Slide builders
// ---------------------------------------------------------------------------

function buildTitleSlide(s) {
  const slide = pptx.addSlide();
  slide.background = { color: BURNT_ORANGE };

  // Headline
  slide.addText(s.headline || data.title || "", {
    x: 0.8, y: 1.0, w: 11.5, h: 2.5,
    fontSize: 40, fontFace: "Arial", bold: true,
    color: WHITE, align: "left", valign: "bottom",
    isTextBox: true
  });

  // White divider line
  slide.addShape(pptx.ShapeType.line, {
    x: 0.8, y: 3.7, w: 5.0, h: 0,
    line: { color: WHITE, width: 1.5 }
  });

  // Subtitle
  if (s.subtitle) {
    slide.addText(s.subtitle, {
      x: 0.8, y: 3.9, w: 11.5, h: 0.5,
      fontSize: 20, fontFace: "Arial", color: WHITE,
      align: "left", valign: "top"
    });
  }

  // Presenter
  if (s.presenter) {
    const presenterText = [
      { text: s.presenter, options: { bold: true, fontSize: 16, fontFace: "Arial", color: WHITE } }
    ];
    if (s.presenterTitle) {
      presenterText.push({ text: "\n" + s.presenterTitle, options: { fontSize: 14, fontFace: "Arial", color: WHITE } });
    }
    slide.addText(presenterText, {
      x: 0.8, y: 4.6, w: 11.5, h: 0.8,
      align: "left", valign: "top"
    });
  }

  // Date
  if (s.date) {
    slide.addText(s.date, {
      x: 0.8, y: 5.6, w: 11.5, h: 0.4,
      fontSize: 14, fontFace: "Arial", color: WHITE,
      align: "left"
    });
  }

  addLogo(slide, "white");
}

function buildSectionSlide(s) {
  const slide = pptx.addSlide();
  slide.background = { color: BURNT_ORANGE };

  slide.addText(s.headline || "", {
    x: 1.0, y: 2.0, w: 11.33, h: 2.0,
    fontSize: 36, fontFace: "Arial", bold: true,
    color: WHITE, align: "center", valign: "middle"
  });

  if (s.subtitle) {
    slide.addText(s.subtitle, {
      x: 1.0, y: 4.2, w: 11.33, h: 0.8,
      fontSize: 18, fontFace: "Arial", color: WHITE,
      align: "center", valign: "top"
    });
  }

  addLogo(slide, "white");
}

function buildContentSlide(s) {
  const slide = pptx.addSlide();
  slide.background = { color: WHITE };

  // Title
  slide.addText(s.title || "", {
    x: 0.8, y: 0.4, w: 11.5, h: 0.7,
    fontSize: 28, fontFace: "Arial", bold: true, color: BURNT_ORANGE,
    align: "left", valign: "bottom"
  });

  // Accent line under title
  slide.addShape(pptx.ShapeType.line, {
    x: 0.8, y: 1.2, w: 11.5, h: 0,
    line: { color: BURNT_ORANGE, width: 1.5 }
  });

  // Bullets
  if (s.bullets && s.bullets.length > 0) {
    const bulletText = s.bullets.map(b => ({
      text: b,
      options: { fontSize: 22, fontFace: "Arial", color: CHARCOAL, bullet: { type: "bullet", color: BURNT_ORANGE }, paraSpaceAfter: 12 }
    }));
    slide.addText(bulletText, {
      x: 0.8, y: 1.5, w: 11.5, h: 4.5,
      valign: "top", paraSpaceBefore: 6
    });
  }

  // Body text (non-bullet)
  if (s.body) {
    slide.addText(s.body, {
      x: 0.8, y: 1.5, w: 11.5, h: 4.5,
      fontSize: 20, fontFace: "Arial", color: CHARCOAL,
      align: "left", valign: "top", lineSpacingMultiple: 1.3
    });
  }

  if (s.footnote) addFootnote(slide, s.footnote);
  addLogo(slide, "color");
}

function buildQuestionSlide(s) {
  const slide = pptx.addSlide();
  slide.background = { color: WHITE };

  // Small label
  slide.addText("DISCUSSION", {
    x: 0.8, y: 1.0, w: 11.5, h: 0.4,
    fontSize: 14, fontFace: "Arial", bold: true, color: STEEL_GRAY,
    align: "center"
  });

  // The question — large and centered
  slide.addText(s.question || "", {
    x: 1.0, y: 1.8, w: 11.33, h: 3.0,
    fontSize: 28, fontFace: "Arial", bold: true, color: BURNT_ORANGE,
    align: "center", valign: "middle",
    lineSpacingMultiple: 1.2
  });

  // Subtext
  if (s.subtext) {
    slide.addText(s.subtext, {
      x: 1.5, y: 5.0, w: 10.33, h: 0.6,
      fontSize: 16, fontFace: "Arial", color: STEEL_GRAY, italic: true,
      align: "center"
    });
  }

  addLogo(slide, "color");
}

function buildFrameworkSlide(s) {
  const slide = pptx.addSlide();
  slide.background = { color: WHITE };

  // Title
  slide.addText(s.title || "", {
    x: 0.8, y: 0.4, w: 11.5, h: 0.7,
    fontSize: 28, fontFace: "Arial", bold: true, color: BURNT_ORANGE,
    align: "left"
  });

  slide.addShape(pptx.ShapeType.line, {
    x: 0.8, y: 1.15, w: 11.5, h: 0,
    line: { color: BURNT_ORANGE, width: 1.5 }
  });

  const fw = s.framework;
  const items = s.items || {};

  if (fw === "five_forces") {
    buildFiveForces(slide, items);
  } else if (fw === "vrio") {
    buildVRIO(slide, items);
  } else if (fw === "swot") {
    buildSWOT(slide, items);
  } else {
    // Generic framework — display as labeled items
    buildGenericFramework(slide, items);
  }

  if (s.footnote) addFootnote(slide, s.footnote);
  addLogo(slide, "color");
}

function buildFiveForces(slide, items) {
  const centerX = 4.5, centerY = 3.2, boxW = 4.0, boxH = 0.9;

  // Center: Rivalry
  slide.addShape(pptx.ShapeType.rect, {
    x: centerX, y: centerY, w: boxW, h: boxH,
    fill: { color: BURNT_ORANGE }, rectRadius: 0.05
  });
  slide.addText("Rivalry\n" + (items.rivalry || ""), {
    x: centerX, y: centerY, w: boxW, h: boxH,
    fontSize: 11, fontFace: "Arial", color: WHITE, bold: false,
    align: "center", valign: "middle", lineSpacingMultiple: 1.1
  });

  // Top: New Entrants
  const topY = 1.5;
  slide.addShape(pptx.ShapeType.rect, {
    x: centerX, y: topY, w: boxW, h: boxH,
    fill: { color: LIGHT_BG }, line: { color: STEEL_GRAY, width: 1 }, rectRadius: 0.05
  });
  slide.addText("Threat of New Entrants\n" + (items.newEntrants || ""), {
    x: centerX, y: topY, w: boxW, h: boxH,
    fontSize: 10, fontFace: "Arial", color: CHARCOAL,
    align: "center", valign: "middle", lineSpacingMultiple: 1.1
  });

  // Bottom: Substitutes
  const botY = 5.0;
  slide.addShape(pptx.ShapeType.rect, {
    x: centerX, y: botY, w: boxW, h: boxH,
    fill: { color: LIGHT_BG }, line: { color: STEEL_GRAY, width: 1 }, rectRadius: 0.05
  });
  slide.addText("Threat of Substitutes\n" + (items.substitutes || ""), {
    x: centerX, y: botY, w: boxW, h: boxH,
    fontSize: 10, fontFace: "Arial", color: CHARCOAL,
    align: "center", valign: "middle", lineSpacingMultiple: 1.1
  });

  // Left: Supplier Power
  const leftX = 0.5;
  slide.addShape(pptx.ShapeType.rect, {
    x: leftX, y: centerY, w: 3.5, h: boxH,
    fill: { color: LIGHT_BG }, line: { color: STEEL_GRAY, width: 1 }, rectRadius: 0.05
  });
  slide.addText("Supplier Power\n" + (items.supplierPower || ""), {
    x: leftX, y: centerY, w: 3.5, h: boxH,
    fontSize: 10, fontFace: "Arial", color: CHARCOAL,
    align: "center", valign: "middle", lineSpacingMultiple: 1.1
  });

  // Right: Buyer Power
  const rightX = 9.0;
  slide.addShape(pptx.ShapeType.rect, {
    x: rightX, y: centerY, w: 3.5, h: boxH,
    fill: { color: LIGHT_BG }, line: { color: STEEL_GRAY, width: 1 }, rectRadius: 0.05
  });
  slide.addText("Buyer Power\n" + (items.buyerPower || ""), {
    x: rightX, y: centerY, w: 3.5, h: boxH,
    fontSize: 10, fontFace: "Arial", color: CHARCOAL,
    align: "center", valign: "middle", lineSpacingMultiple: 1.1
  });

  // Arrows (simple lines connecting boxes)
  // Top arrow (down to center)
  slide.addShape(pptx.ShapeType.line, {
    x: centerX + boxW / 2, y: topY + boxH, w: 0, h: centerY - topY - boxH,
    line: { color: STEEL_GRAY, width: 1.5 }
  });
  // Bottom arrow (up to center)
  slide.addShape(pptx.ShapeType.line, {
    x: centerX + boxW / 2, y: centerY + boxH, w: 0, h: botY - centerY - boxH,
    line: { color: STEEL_GRAY, width: 1.5 }
  });
  // Left arrow
  slide.addShape(pptx.ShapeType.line, {
    x: leftX + 3.5, y: centerY + boxH / 2, w: centerX - leftX - 3.5, h: 0,
    line: { color: STEEL_GRAY, width: 1.5 }
  });
  // Right arrow
  slide.addShape(pptx.ShapeType.line, {
    x: centerX + boxW, y: centerY + boxH / 2, w: rightX - centerX - boxW, h: 0,
    line: { color: STEEL_GRAY, width: 1.5 }
  });
}

function buildVRIO(slide, items) {
  const labels = ["Valuable", "Rare", "Inimitable", "Organized"];
  const keys = ["valuable", "rare", "inimitable", "organized"];
  const startY = 1.5;
  const rowH = 1.1;

  labels.forEach((label, i) => {
    const y = startY + i * (rowH + 0.15);
    // Label box
    slide.addShape(pptx.ShapeType.rect, {
      x: 0.8, y, w: 2.5, h: rowH,
      fill: { color: BURNT_ORANGE }, rectRadius: 0.05
    });
    slide.addText(label, {
      x: 0.8, y, w: 2.5, h: rowH,
      fontSize: 18, fontFace: "Arial", bold: true, color: WHITE,
      align: "center", valign: "middle"
    });
    // Content box
    slide.addShape(pptx.ShapeType.rect, {
      x: 3.5, y, w: 8.83, h: rowH,
      fill: { color: LIGHT_BG }, line: { color: STEEL_GRAY, width: 0.5 }, rectRadius: 0.05
    });
    slide.addText(items[keys[i]] || "", {
      x: 3.7, y, w: 8.5, h: rowH,
      fontSize: 14, fontFace: "Arial", color: CHARCOAL,
      align: "left", valign: "middle", lineSpacingMultiple: 1.1
    });
  });
}

function buildSWOT(slide, items) {
  const labels = [
    { key: "strengths", label: "Strengths", x: 0.8, y: 1.5 },
    { key: "weaknesses", label: "Weaknesses", x: 6.75, y: 1.5 },
    { key: "opportunities", label: "Opportunities", x: 0.8, y: 4.0 },
    { key: "threats", label: "Threats", x: 6.75, y: 4.0 }
  ];
  const boxW = 5.75, boxH = 2.2;

  labels.forEach(({ key, label, x, y }) => {
    slide.addShape(pptx.ShapeType.rect, {
      x, y, w: boxW, h: boxH,
      fill: { color: LIGHT_BG }, line: { color: STEEL_GRAY, width: 0.5 }, rectRadius: 0.05
    });
    slide.addText(label, {
      x, y, w: boxW, h: 0.45,
      fontSize: 16, fontFace: "Arial", bold: true, color: BURNT_ORANGE,
      align: "center", valign: "middle"
    });
    const content = items[key];
    const text = Array.isArray(content) ? content.join("\n") : (content || "");
    slide.addText(text, {
      x: x + 0.2, y: y + 0.5, w: boxW - 0.4, h: boxH - 0.6,
      fontSize: 12, fontFace: "Arial", color: CHARCOAL,
      align: "left", valign: "top", lineSpacingMultiple: 1.2
    });
  });
}

function buildGenericFramework(slide, items) {
  const keys = Object.keys(items);
  const startY = 1.5;
  const rowH = Math.min(1.0, 5.0 / keys.length);

  keys.forEach((key, i) => {
    const y = startY + i * (rowH + 0.1);
    const label = key.replace(/([A-Z])/g, " $1").replace(/^./, s => s.toUpperCase());
    slide.addText(label + ":", {
      x: 0.8, y, w: 3.0, h: rowH,
      fontSize: 16, fontFace: "Arial", bold: true, color: BURNT_ORANGE,
      align: "left", valign: "middle"
    });
    slide.addText(items[key] || "", {
      x: 4.0, y, w: 8.33, h: rowH,
      fontSize: 14, fontFace: "Arial", color: CHARCOAL,
      align: "left", valign: "middle", lineSpacingMultiple: 1.1
    });
  });
}

function buildTwoColumnSlide(s) {
  const slide = pptx.addSlide();
  slide.background = { color: WHITE };

  // Title
  slide.addText(s.title || "", {
    x: 0.8, y: 0.4, w: 11.5, h: 0.7,
    fontSize: 28, fontFace: "Arial", bold: true, color: BURNT_ORANGE,
    align: "left"
  });

  slide.addShape(pptx.ShapeType.line, {
    x: 0.8, y: 1.15, w: 11.5, h: 0,
    line: { color: BURNT_ORANGE, width: 1.5 }
  });

  // Left column
  const colW = 5.5;
  if (s.leftHeading) {
    slide.addText(s.leftHeading, {
      x: 0.8, y: 1.4, w: colW, h: 0.5,
      fontSize: 20, fontFace: "Arial", bold: true, color: CHARCOAL,
      align: "left"
    });
  }
  if (s.leftBullets) {
    const leftText = s.leftBullets.map(b => ({
      text: b,
      options: { fontSize: 18, fontFace: "Arial", color: CHARCOAL, bullet: { type: "bullet", color: BURNT_ORANGE }, paraSpaceAfter: 8 }
    }));
    slide.addText(leftText, {
      x: 0.8, y: 2.0, w: colW, h: 4.0,
      valign: "top"
    });
  }

  // Divider line
  slide.addShape(pptx.ShapeType.line, {
    x: 6.66, y: 1.5, w: 0, h: 4.5,
    line: { color: WARM_GRAY, width: 1 }
  });

  // Right column
  if (s.rightHeading) {
    slide.addText(s.rightHeading, {
      x: 7.0, y: 1.4, w: colW, h: 0.5,
      fontSize: 20, fontFace: "Arial", bold: true, color: CHARCOAL,
      align: "left"
    });
  }
  if (s.rightBullets) {
    const rightText = s.rightBullets.map(b => ({
      text: b,
      options: { fontSize: 18, fontFace: "Arial", color: CHARCOAL, bullet: { type: "bullet", color: BURNT_ORANGE }, paraSpaceAfter: 8 }
    }));
    slide.addText(rightText, {
      x: 7.0, y: 2.0, w: colW, h: 4.0,
      valign: "top"
    });
  }

  if (s.footnote) addFootnote(slide, s.footnote);
  addLogo(slide, "color");
}

function buildOptionsSlide(s) {
  const slide = pptx.addSlide();
  slide.background = { color: WHITE };

  slide.addText(s.title || "Strategic Options", {
    x: 0.8, y: 0.4, w: 11.5, h: 0.7,
    fontSize: 28, fontFace: "Arial", bold: true, color: BURNT_ORANGE,
    align: "left"
  });

  slide.addShape(pptx.ShapeType.line, {
    x: 0.8, y: 1.15, w: 11.5, h: 0,
    line: { color: BURNT_ORANGE, width: 1.5 }
  });

  const options = s.options || [];
  const optH = Math.min(1.4, 5.0 / options.length);
  const startY = 1.5;

  options.forEach((opt, i) => {
    const y = startY + i * (optH + 0.15);

    // Number circle
    slide.addShape(pptx.ShapeType.ellipse, {
      x: 0.8, y: y + 0.1, w: 0.55, h: 0.55,
      fill: { color: BURNT_ORANGE }
    });
    slide.addText(String(i + 1), {
      x: 0.8, y: y + 0.1, w: 0.55, h: 0.55,
      fontSize: 20, fontFace: "Arial", bold: true, color: WHITE,
      align: "center", valign: "middle"
    });

    // Option name
    slide.addText(opt.name || "", {
      x: 1.6, y, w: 10.5, h: 0.5,
      fontSize: 22, fontFace: "Arial", bold: true, color: CHARCOAL,
      align: "left", valign: "bottom"
    });

    // Description
    slide.addText(opt.description || "", {
      x: 1.6, y: y + 0.5, w: 10.5, h: optH - 0.5,
      fontSize: 16, fontFace: "Arial", color: STEEL_GRAY,
      align: "left", valign: "top", lineSpacingMultiple: 1.2
    });
  });

  addLogo(slide, "color");
}

function buildQuoteSlide(s) {
  const slide = pptx.addSlide();
  slide.background = { color: LIGHT_BG };

  // Large open quote mark
  slide.addText("\u201C", {
    x: 1.0, y: 1.0, w: 1.5, h: 1.5,
    fontSize: 96, fontFace: "Georgia", color: BURNT_ORANGE,
    align: "left", valign: "top"
  });

  // Quote text
  slide.addText(s.quote || "", {
    x: 1.5, y: 2.2, w: 10.33, h: 2.5,
    fontSize: 28, fontFace: "Georgia", italic: true, color: CHARCOAL,
    align: "center", valign: "middle",
    lineSpacingMultiple: 1.3
  });

  // Attribution
  if (s.attribution) {
    slide.addText("\u2014 " + s.attribution, {
      x: 1.5, y: 5.0, w: 10.33, h: 0.5,
      fontSize: 16, fontFace: "Arial", color: STEEL_GRAY,
      align: "center"
    });
  }

  addLogo(slide, "color");
}

function buildDataSlide(s) {
  const slide = pptx.addSlide();
  slide.background = { color: WHITE };

  slide.addText(s.title || "", {
    x: 0.8, y: 0.4, w: 11.5, h: 0.7,
    fontSize: 28, fontFace: "Arial", bold: true, color: BURNT_ORANGE,
    align: "left"
  });

  slide.addShape(pptx.ShapeType.line, {
    x: 0.8, y: 1.15, w: 11.5, h: 0,
    line: { color: BURNT_ORANGE, width: 1.5 }
  });

  // Data points as large metrics
  const points = s.dataPoints || [];
  const numPoints = points.length;
  const colW = Math.min(3.5, 11.5 / numPoints);
  const startX = (13.33 - colW * numPoints) / 2;

  points.forEach((dp, i) => {
    const x = startX + i * colW;

    // Value (large)
    slide.addText(dp.value || "", {
      x, y: 2.0, w: colW, h: 1.8,
      fontSize: 44, fontFace: "Arial", bold: true, color: BURNT_ORANGE,
      align: "center", valign: "bottom"
    });

    // Label
    slide.addText(dp.label || "", {
      x, y: 3.9, w: colW, h: 0.6,
      fontSize: 16, fontFace: "Arial", color: CHARCOAL,
      align: "center", valign: "top"
    });

    // Sublabel
    if (dp.sublabel) {
      slide.addText(dp.sublabel, {
        x, y: 4.5, w: colW, h: 0.4,
        fontSize: 12, fontFace: "Arial", color: STEEL_GRAY,
        align: "center"
      });
    }
  });

  if (s.footnote) addFootnote(slide, s.footnote);
  addLogo(slide, "color");
}

function buildTakeawaySlide(s) {
  const slide = pptx.addSlide();
  slide.background = { color: WHITE };

  slide.addText(s.title || "Key Takeaways", {
    x: 0.8, y: 0.4, w: 11.5, h: 0.7,
    fontSize: 28, fontFace: "Arial", bold: true, color: BURNT_ORANGE,
    align: "left"
  });

  slide.addShape(pptx.ShapeType.line, {
    x: 0.8, y: 1.15, w: 11.5, h: 0,
    line: { color: BURNT_ORANGE, width: 1.5 }
  });

  if (s.bullets) {
    const bulletText = s.bullets.map((b, i) => ({
      text: b,
      options: {
        fontSize: 22, fontFace: "Arial", color: CHARCOAL,
        bullet: { type: "number", color: BURNT_ORANGE },
        paraSpaceAfter: 14
      }
    }));
    slide.addText(bulletText, {
      x: 0.8, y: 1.5, w: 11.5, h: 5.0,
      valign: "top"
    });
  }

  addLogo(slide, "color");
}

function buildNextSlide(s) {
  const slide = pptx.addSlide();
  slide.background = { color: CHARCOAL };

  slide.addText(s.title || "Next Class", {
    x: 0.8, y: 1.5, w: 11.5, h: 1.0,
    fontSize: 36, fontFace: "Arial", bold: true, color: WHITE,
    align: "center", valign: "bottom"
  });

  // White divider
  slide.addShape(pptx.ShapeType.line, {
    x: 4.5, y: 2.8, w: 4.33, h: 0,
    line: { color: BURNT_ORANGE, width: 2 }
  });

  if (s.content) {
    slide.addText(s.content, {
      x: 1.5, y: 3.2, w: 10.33, h: 2.5,
      fontSize: 20, fontFace: "Arial", color: WHITE,
      align: "center", valign: "top",
      lineSpacingMultiple: 1.4
    });
  }

  addLogo(slide, "white");
}

function buildBlankSlide(s) {
  const slide = pptx.addSlide();
  slide.background = { color: WHITE };
  if (s.title) {
    slide.addText(s.title, {
      x: 0.8, y: 0.4, w: 11.5, h: 0.7,
      fontSize: 28, fontFace: "Arial", bold: true, color: BURNT_ORANGE,
      align: "left"
    });
  }
  addLogo(slide, "color");
}

// ---------------------------------------------------------------------------
// Dispatch
// ---------------------------------------------------------------------------
const builders = {
  title: buildTitleSlide,
  section: buildSectionSlide,
  content: buildContentSlide,
  question: buildQuestionSlide,
  framework: buildFrameworkSlide,
  two_column: buildTwoColumnSlide,
  options: buildOptionsSlide,
  quote: buildQuoteSlide,
  data: buildDataSlide,
  takeaway: buildTakeawaySlide,
  next: buildNextSlide,
  blank: buildBlankSlide,
};

// ---------------------------------------------------------------------------
// Generate
// ---------------------------------------------------------------------------
async function main() {
  const slides = data.slides || [];
  for (const s of slides) {
    const builder = builders[s.type];
    if (builder) {
      builder(s);
    } else {
      console.warn(`Unknown slide type: ${s.type} — skipping`);
    }
  }

  await pptx.writeFile({ fileName: outputPath });
  console.log("Presentation created: " + outputPath);
}

main().catch(err => {
  console.error("Error generating presentation:", err);
  process.exit(1);
});
