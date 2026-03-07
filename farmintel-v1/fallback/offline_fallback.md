# Offline Intelligence Mode

When tools fail or network is unavailable, the system collects information directly from the user through guided questions.

## Weather Questions

When user asks about weather:
- What is the current temperature?
- What season is it?
- Is there rainfall expected?
- What is the humidity level?
- What is the wind speed?

**Offline Response:** Provide general weather-based farming advice based on user answers

## Soil Questions

When user asks about soil:
- What is your soil type? (sandy / clay / loamy / mixed)
- What is the soil pH? (acidic / neutral / alkaline)
- Have you done a soil test?
- What color is your soil?
- Is the soil well-draining?

**Offline Response:** Provide soil management recommendations based on answers

## Crop Questions

When user asks about crops:
- Which crop are you growing?
- What stage is the crop in? (seedling / vegetative / flowering / fruiting / harvest)
- How long has it been growing?
- What is the soil condition?
- Are you seeing any symptoms?

**Offline Response:** Provide crop-specific advice based on growth stage

## Pest Questions

When user asks about pests:
- What symptoms do you see?
  - Leaf spots
  - Yellow leaves
  - Holes in leaves
  - Wilting
  - Sticky residue
  - Webbing
- Where are the pests? (leaves / stems / roots / fruits)
- How widespread is the infestation?

**Offline Response:** Provide organic and chemical pest control recommendations

## Disease Questions

When user asks about diseases:
- What are the symptoms?
  - Brown spots
  - Yellow patches
  - Wilting
  - Rotting
  - Powdery coating
- Which part of plant is affected? (leaves / stems / roots / fruits)
- How quickly is it spreading?

**Offline Response:** Provide disease identification and treatment options

## Irrigation Questions

When user asks about watering:
- How often are you watering?
- What is the soil moisture? (wet / moist / dry)
- What is the weather like?
- What crop are you growing?
- What is the soil type?

**Offline Response:** Provide irrigation frequency and method recommendations

## Fertilizer Questions

When user asks about fertilizers:
- What is the crop?
- What stage is the crop in?
- Have you done a soil test?
- What fertilizers do you have available?
- What is your budget?

**Offline Response:** Provide organic and chemical fertilizer recommendations

## Harvest Questions

When user asks about harvesting:
- What crop are you growing?
- How long has it been growing?
- What is the current condition?
- Do you have storage facilities?
- What is your market?

**Offline Response:** Provide harvest timing and post-harvest handling advice

## Fallback Response Strategy

1. **Collect Information:** Ask guided questions
2. **Analyze Answers:** Match against knowledge base
3. **Generate Response:** Provide best-match advice
4. **Suggest Online:** Recommend connecting to internet for real-time data
5. **Cache Response:** Store for future offline use

## Offline Knowledge Base

### Crop Stages
- Seedling: 0-3 weeks
- Vegetative: 3-8 weeks
- Flowering: 8-12 weeks
- Fruiting: 12-16 weeks
- Maturation: 16+ weeks

### Soil Types
- Sandy: Fast draining, low nutrients
- Clay: Slow draining, high nutrients
- Loamy: Balanced, ideal for most crops
- Mixed: Variable properties

### Common Symptoms
- Yellow leaves: Nitrogen deficiency or disease
- Brown spots: Fungal infection
- Wilting: Water stress or root disease
- Holes: Pest damage
- Sticky residue: Aphid or scale infestation
