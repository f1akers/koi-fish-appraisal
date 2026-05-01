# Formula Updates

## Goal

- We will refactor usage of formula in getting scores for Color and Symmetry for our Koi Analysis
- Use codebase-architect to know the current structure and formula

## Formula for solving symmetry

### Topic

- use @doi-topic-research and adapt it to research in MDPI.com (still similar) to research this topic (link)[https://www.mdpi.com/2410-3888/7/4/158]
- Split the koi into 5 parts, and use the longitudinal pattern distribution, etc. The formula is described there
- Derive a score from this

## Formula for color

- We have ideal values, based on the distribution of the analyzed image, these ideal values will be used to derive a score

### Sanke

- Red = 50%, White = 30%, Blue = 20%
- Ogon: Uniform Color 100%
- Kohaku: Red = 60, White = 40%

## Overall Score

Use the color and symmetry to derive an overall score, make sure you only derive from these two.

### Name change

- Replace any title reference to "ShowKoi", with the description: "AI-Powered Fish Quality Assessment"

## Execution

- Use Sonnet 4.6 for Execution
- The agents for research are using Opus 4.6
