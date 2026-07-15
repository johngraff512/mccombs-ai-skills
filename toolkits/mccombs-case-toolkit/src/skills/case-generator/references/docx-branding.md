# McCombs Case Document Formatting Specifications

These specifications are derived from the official McCombs_Basic.dotx template. Follow them exactly when generating case .docx files.

## Page Setup

| Property | Value | DXA |
|----------|-------|-----|
| Page width | 8.5 inches | 12240 |
| Page height | 11 inches | 15840 |
| Top margin | 1.0 inches | 1440 |
| Bottom margin | 0.8 inches | 1152 |
| Left margin | 0.8 inches | 1152 |
| Right margin | 0.8 inches | 1152 |
| Content width | 6.9 inches | 9936 |

The increased top margin (1.0 inch) provides breathing room below the McCombs logo header, and the increased bottom margin (0.8 inch) prevents body text from crowding the footer.

## Brand Colors

| Element | Color | Hex |
|---------|-------|-----|
| Headings (H1-H4) | Burnt Orange | `#BF5700` |
| Headings (H5-H6) | Steel Gray | `#989EA3` |
| Body text | Charcoal | `#333F48` |
| Table header background | Burnt Orange | `#BF5700` |
| Table header text | White | `#FFFFFF` |
| Table alternating rows | Light Warm Gray | `#F5F4F2` |
| Accent/highlight | Burnt Orange | `#BF5700` |

Note: The McCombs template uses `#BF5700` (not `#C05900` which is used in slides). Use `#BF5700` for all document headings and accents.

## Typography

### Font Stack
- **Body text**: Arial, 12pt (24 half-points)
- **Default font in template**: Open Sans (fallback), but Normal style overrides to Arial
- **Line spacing**: 1.5 lines (360 twentieths of a line)

### Heading Styles

| Style | Font | Size | Weight | Case | Color | Spacing Before |
|-------|------|------|--------|------|-------|----------------|
| Title | Arial | 28pt (56) | Regular | Normal | #BF5700 | 0 |
| Heading 1 | Arial | 16pt (32) | Bold | Normal | #BF5700 | 240 twips |
| Heading 2 | Arial | 13pt (26) | Regular | ALL CAPS | #BF5700 | 40 twips |
| Heading 3 | Arial | 12pt (24) | Bold | ALL CAPS | #BF5700 | 120 twips |
| Heading 4 | Arial | 12pt (24) | Regular | Normal | #BF5700 | 120 twips |
| Body | Arial | 12pt (24) | Regular | Normal | #333F48 | 0 |

### docx-js Style Definitions

```javascript
styles: {
  default: {
    document: {
      run: { font: "Arial", size: 24, color: "333F48" }
    }
  },
  paragraphStyles: [
    {
      id: "Title", name: "Title", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: "Arial", size: 56, color: "BF5700", characterSpacing: -10 },
      paragraph: { spacing: { after: 200 } }
    },
    {
      id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: "Arial", size: 32, bold: true, color: "BF5700" },
      paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, keepLines: true, outlineLevel: 0 }
    },
    {
      id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: "Arial", size: 26, color: "BF5700", allCaps: true },
      paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, keepLines: true, outlineLevel: 1 }
    },
    {
      id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: "Arial", size: 24, bold: true, color: "BF5700", allCaps: true },
      paragraph: { spacing: { before: 120, after: 60 }, keepNext: true, keepLines: true, outlineLevel: 2 }
    }
  ]
}
```

## Header

The header contains the McCombs School of Business logo:
- Image file: `assets/mccombs_logo.png`
- Width: 3 inches (approximately 2743200 EMUs or 4320 DXA)
- Positioned at left with a negative indent of -576 DXA (to align with left edge despite margins)
- The logo image is approximately 2743200 x 343695 EMUs

In docx-js, create a header with the logo image:
```javascript
headers: {
  default: new Header({
    children: [
      new Paragraph({
        children: [
          new ImageRun({
            type: "png",
            data: fs.readFileSync("<path-to-skill>/assets/mccombs_logo.png"),
            transformation: { width: 216, height: 27 },
            altText: { title: "McCombs School of Business", description: "McCombs School of Business logo", name: "McCombs Logo" }
          })
        ]
      })
    ]
  })
}
```

## Title Block Accent

After the subtitle/meta line and before the learning objectives or first body section, insert a Burnt Orange horizontal rule to visually separate the title block from the case content:

```javascript
new Paragraph({
  spacing: { before: 200, after: 200 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "BF5700", space: 1 } },
  children: []
})
```

This accent line signals the transition from metadata to case narrative and adds visual polish consistent with McCombs brand materials.

## Footer

The footer includes the McCombs branding line and page numbers. Use centered alignment and small text (8pt):

```javascript
footers: {
  default: new Footer({
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        children: [
          new TextRun({ text: "McCombs School of Business  |  The University of Texas at Austin", font: "Arial", size: 16, color: "999999" }),
          new TextRun({ text: "\t", font: "Arial", size: 16 }),
          new TextRun({ text: "Page ", font: "Arial", size: 16, color: "999999" }),
          new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "999999" }),
        ]
      })
    ]
  })
}
```

Always include page numbers for cases longer than 3 pages — faculty and students need them for class discussion references.

## Table Formatting

When cases include exhibit tables:

```javascript
// Header row
new TableRow({
  children: cells.map(text => new TableCell({
    shading: { fill: "BF5700", type: ShadingType.CLEAR },
    borders: borders,
    width: { size: cellWidth, type: WidthType.DXA },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      children: [new TextRun({ text, bold: true, color: "FFFFFF", font: "Arial", size: 20 })]
    })]
  }))
})

// Alternating data rows
// Even rows: no shading (white)
// Odd rows: shading fill "F5F4F2"
```

Use `WidthType.DXA` for all table widths. Full-width tables should be 9936 DXA.

When exhibit tables have columns with longer text content (like descriptions or differentiators), consider using landscape orientation for that page section, or reduce the number of columns and split into multiple tables. Heavily wrapped text in narrow columns looks unprofessional.

## Footnotes

Use Word's native footnote system for inline source citations. Footnotes appear at the bottom of the page where they are referenced, numbered automatically by Word.

**docx-js API:**
```javascript
const { FootnoteReferenceRun } = require("docx");

// In a paragraph's runs array, insert the reference after the claim:
new Paragraph({
  children: [
    new TextRun({ text: "Lisa Su described this as the 'YottaScale' era", font: "Arial", size: 24, color: "333F48" }),
    new FootnoteReferenceRun(1),  // IMPORTANT: pass integer directly, NOT { id: 1 } — object form generates invalid XML
    new TextRun({ text: " — a reference to compute capacity expected over five years.", font: "Arial", size: 24, color: "333F48" }),
  ]
})

// In the Document constructor, pass the footnotes map:
new Document({
  footnotes: {
    1: {
      children: [
        new Paragraph({
          children: [new TextRun({ text: "Lisa Su, AMD CES 2026 Keynote, January 6, 2026. ...", font: "Arial", size: 18, color: "333F48" })]
        })
      ]
    }
  },
  sections: [...]
})
```

**JSON schema for the reusable script:**
```json
"footnotes": {
  "1": "Full footnote text. Include full citation.",
  "2": "Another footnote."
}
```

Footnote text renders in 9pt Arial. Keep footnotes concise — one to three sentences. If a source requires a full bibliographic entry, include a short footnote and add the full entry to the Sources section.

## Document Structure for a Business Case

The typical document structure, in order:

1. **Header** with McCombs logo (on every page)
2. **Title** (case name) — use Title style
3. **Subtitle line** — course name, date, author (optional)
4. **Burnt Orange accent rule** — horizontal line separating title block from body
5. **Learning Objectives** — bulleted list of 2-5 Bloom's taxonomy-aligned objectives
6. **Body sections** using Heading 1 for major sections, Heading 2 for subsections
7. **Exhibits** section — tables and data, each labeled "Exhibit 1:", "Exhibit 2:", etc.
8. **Sources** section — numbered or bulleted list of references
9. **Footer** with McCombs branding and page numbers (on every page)

## Important Notes

- Always set page size explicitly to US Letter (not A4)
- Use `ShadingType.CLEAR` for table cell shading, never `SOLID`
- Set `xml:space="preserve"` on text runs with leading/trailing whitespace
- Never use unicode bullets — use proper numbering config with `LevelFormat.BULLET`
- Validate the document after generation if a validation script is available
