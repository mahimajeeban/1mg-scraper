# LLM Extraction Rules for 1mg Product Pages

This document defines intelligent extraction rules for the Gemini LLM when parsing product data from 1mg.com.

---

## Composition/Ingredients Detection

### Problem
Different product types on 1mg use different labels for essentially the same concept (what the product is made of):

| Product Type | Label Used | Example URL |
|---|---|---|
| Prescription drugs | `SALT COMPOSITION` | `/drugs/manforce-staylong-tablet-369128` |
| OTC cosmetics/soaps | `Key Ingredients:` | `/otc/venusia-cleansing-moisturising-bathing-bar-...` |
| Supplements/vitamins | `Key Ingredients:` | Becosules Z Capsule |
| Some products | `Composition`, `Ingredients`, `Active Ingredients` | Various |

### Solution
The LLM should intelligently detect composition-like content by looking for ANY of these label patterns:

#### Primary Labels (Most Common)
- **SALT COMPOSITION** → for drugs/medicines
- **Key Ingredients:** → for OTC/cosmetics/supplements

#### Alternative Labels (Less Common)
- Composition
- Ingredients
- Active Ingredients
- Contains
- Key Actives
- Active Substance
- Formulation
- Salt Composition

### Extraction Rules

1. **Search Strategy**: Look for any heading/label on the page that matches the patterns above (case-insensitive)

2. **Content Extraction**: Extract all items listed under that section

3. **Format**: Join multiple items with ` + ` (space-plus-space)
   - Example: `Dapoxetine (30mg) + Sildenafil (50mg)`
   - Example: `Aloe Butter + Shea Butter + Sodium Coco Sulphate + Cetostearyl Alcohol`

4. **Fallback**: If no label found, use `"N/A"`

5. **Critical Rule**: **Do NOT include composition/ingredients in the description field**
   - Composition belongs in its own dedicated column
   - Description should focus on what the product does, not what it contains

---

## Description Generation

### Length Requirement
- **3-4 sentences only** (maximum 60 words total)
- Strict enforcement - no exceptions
- Each sentence should be focused and meaningful
- Avoid repetition and unnecessary details

### Content Guidelines

**What to Include:**
1. What the product is (product category/type)
2. Primary purpose or use
3. Key benefits (2-3 main benefits)
4. Who it is for (target user/condition)
5. How/when to use it (if important)

**What to EXCLUDE:**
- ❌ Composition/ingredients (goes in separate column)
- ❌ Full chemical names and dosages
- ❌ Repetitive marketing language
- ❌ Lengthy disclaimers
- ❌ Storage instructions (unless critical)

### Example Good Description (3-4 sentences, ~60 words)

> Manforce Staylong Tablet is a prescription medicine used to treat premature ejaculation and erectile dysfunction in adult men. It works by delaying ejaculation and improving blood flow to enhance sexual performance. Take 1-3 hours before sexual activity as directed by a doctor. Not suitable for women or children under 18.

### Example Bad Description (too long)

> ❌ Manforce Staylong Tablet contains Dapoxetine and Sildenafil in specific doses. Dapoxetine is a selective serotonin reuptake inhibitor that works by increasing serotonin levels in the nervous system which helps in delaying ejaculation. Sildenafil is a phosphodiesterase-5 inhibitor which works by relaxing the blood vessels in the penis thereby allowing more blood flow when sexually aroused. This medicine should be stored below 30°C in a cool dry place away from sunlight... [continues]

---

## Field Definitions for LLM

When extracting data, the LLM should populate these exact fields:

```json
{
  "medicineName": "Full product name from page title/heading",
  "companyName": "Manufacturer/brand name (default to provided value if unclear)",
  "price": "MRP price as number (e.g., 99.0) or 'N/A'",
  "composition": "Ingredients using smart label detection - MUST scan entire text (see rules above)",
  "summary": "EXACTLY 1-2 sentences (max 30 words)",
  "description": "EXACTLY 3-4 sentences only (max 60 words total) - strict enforcement"
}
```

---

## Final Formatting

The system combines `summary` and `description` in this format:

```
{medicineName}

{summary}

Read More...

{description}
```

This gives users:
1. Product name
2. Quick summary (1-2 sentences, ~30 words)
3. "Read More..." separator
4. Detailed description (3-4 sentences, ~60 words)

Total: ~5-7 lines in final output (concise and meaningful)

---

## Version History

- **v1.1** (June 6, 2026): Strengthened composition extraction and enforced strict word limits on descriptions
- **v1.0** (June 6, 2026): Initial rules based on analysis of Shipla, Mankind, and Pfizer products on 1mg.com
