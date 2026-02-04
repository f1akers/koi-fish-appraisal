**Koi Fish Appraisal through Multiple Factors**

Backend:  
Python: FastAPI \+ OpenCV \+ Ultralytics  
Frontend: Vite React-TS \+ Tailwind

Structure:  
docs/  
frontend/  
backend/

Documentation:  
docs/

- FEATURE\_INDEX.md  
- features/  
- Features list

**Feature 1:** Fish Metrics

All of these metrics will return a numerical value so that we can train a linear regression model by processing a bunch of images, koi fishes that have been appraised by price

**Step 1**  
Size Detection

- Use a trained model for detecting the instance segmentation of koi fish, will be stored at **backend/models/koi-segment.pt** \- detect how many pixels that segment has  
- Use another trained model to detect a reference coin, and gather its size from a stored value key-pair from a python file, model at **backend/models/coin.pt**  
- Use that reference to gather the Pixels Per Centimeter, and then solve for the size of the fish

**Step 2**  
Pattern

- Use the next trained model: **backend/models/koi-pattern.pt**, to determine the pattern from 3 types: **Ogon, Showa, and Kohaku** (ogon, showa, kohaku for class names in the model), these will be the only patterns we’ll focus on.

**Step 3**  
Color

- Use a levels-based approach to determine the color quantity based on those 3 colors, from the best criteria that you can make crafted from data online.

**Step 4**  
Symmetry

- Use a PCA \+ Chi squared approach to compare the left and right sides of the fish from the middle. This is so when they are bent we can still get the symmetry.

**Step 5**  
Price

- From the saved linear regression model, get the comparative numerical value and then process it in the regression model, and return a price.

**Feature 2:** Linear Regression Trainer

Prepare a script to train a linear regression model based on a CSV file:  
**Column 1: image file name**, must be stored at backend/images/  
**Column 2:** **price**  
Process and save the model to **backend/models/linear.\[whatever extension this is\]**

**Frontend Features**

- Frontend will get the camera of the user, pointing at a point in the pond that they will put the koi fish under, which coin will be there too in the scene, press a “Capture” button, this will capture an image, and appraise the fish  
- Frontend will also show the individual metrics that it based on to generate price, if possible there's a graph to show the linear regression of prices, and where that image captured of koi fish lies on that graph  
- Export to CSV