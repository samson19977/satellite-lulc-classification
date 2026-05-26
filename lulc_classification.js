// ============================================================
//  Land Use / Land Cover Classification — Google Earth Engine
//  Author  : Your Name
//  Region  : Lake Victoria Basin, East Africa (customisable)
//  Sensor  : Sentinel-2 SR (10 m)
//  Method  : Random Forest supervised classification
// ============================================================

// ── 0. STUDY AREA ───────────────────────────────────────────
var roi = ee.Geometry.Rectangle([31.5, -2.5, 35.0, 1.0]);
Map.centerObject(roi, 8);
Map.setOptions('SATELLITE');

// ── 1. LOAD & PREPROCESS SENTINEL-2 ─────────────────────────
function maskS2clouds(image) {
  var qa = image.select('QA60');
  var cloudBitMask = 1 << 10;
  var cirrusBitMask = 1 << 11;
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
               .and(qa.bitwiseAnd(cirrusBitMask).eq(0));
  return image.updateMask(mask).divide(10000)
              .copyProperties(image, ['system:time_start']);
}

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(roi)
  .filterDate('2023-01-01', '2023-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(maskS2clouds)
  .median()
  .clip(roi);

// ── 2. SPECTRAL INDICES ──────────────────────────────────────
var ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI');
var ndwi = s2.normalizedDifference(['B3', 'B8']).rename('NDWI');
var ndbi = s2.normalizedDifference(['B11', 'B8']).rename('NDBI');
var evi  = s2.expression(
  '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
  { NIR: s2.select('B8'), RED: s2.select('B4'), BLUE: s2.select('B2') }
).rename('EVI');

// ── 3. BUILD COMPOSITE ──────────────────────────────────────
var composite = s2.select(['B2','B3','B4','B8','B11','B12'])
                  .addBands([ndvi, ndwi, ndbi, evi]);

// ── 4. TRAINING SAMPLES ──────────────────────────────────────
// *** Replace these with your own digitised polygons ***
var water      = ee.FeatureCollection('users/YOUR_USER/lulc/water');
var forest     = ee.FeatureCollection('users/YOUR_USER/lulc/forest');
var cropland   = ee.FeatureCollection('users/YOUR_USER/lulc/cropland');
var urban      = ee.FeatureCollection('users/YOUR_USER/lulc/urban');
var grassland  = ee.FeatureCollection('users/YOUR_USER/lulc/grassland');

// Class labels  0=Water 1=Forest 2=Cropland 3=Urban 4=Grassland
var trainingData = water.merge(forest).merge(cropland)
                        .merge(urban).merge(grassland);

var training = composite.sampleRegions({
  collection : trainingData,
  properties : ['class'],
  scale      : 10
});

// ── 5. TRAIN RANDOM FOREST ───────────────────────────────────
var classifier = ee.Classifier.smileRandomForest({
  numberOfTrees      : 100,
  variablesPerSplit  : 4,
  minLeafPopulation  : 5,
  bagFraction        : 0.7,
  seed               : 42
}).train({
  features  : training,
  classProperty : 'class',
  inputProperties : composite.bandNames()
});

// ── 6. CLASSIFY ──────────────────────────────────────────────
var classified = composite.classify(classifier);

// ── 7. ACCURACY ASSESSMENT ───────────────────────────────────
var split      = training.randomColumn('random', 42);
var trainSet   = split.filter(ee.Filter.lt('random', 0.7));
var testSet    = split.filter(ee.Filter.gte('random', 0.7));

var validated  = testSet.classify(
  ee.Classifier.smileRandomForest(100).train({
    features       : trainSet,
    classProperty  : 'class',
    inputProperties: composite.bandNames()
  })
);

var errorMatrix = validated.errorMatrix('class', 'classification');
print('Confusion Matrix', errorMatrix);
print('Overall Accuracy', errorMatrix.accuracy());
print('Kappa Coefficient', errorMatrix.kappa());
print('Consumer Accuracy (Recall)',  errorMatrix.consumersAccuracy());
print('Producer Accuracy (Precision)', errorMatrix.producersAccuracy());

// ── 8. VISUALISATION ─────────────────────────────────────────
var palette = ['#1a6faf', '#228b22', '#f5c518', '#e74c3c', '#90ee90'];
var lulcVis = { min: 0, max: 4, palette: palette };

Map.addLayer(s2, { bands:['B4','B3','B2'], min:0.0, max:0.3 }, 'True Colour');
Map.addLayer(ndvi, { min:-0.2, max:0.8, palette:['brown','white','darkgreen'] }, 'NDVI');
Map.addLayer(classified, lulcVis, 'LULC Classification');

// ── 9. LEGEND ────────────────────────────────────────────────
var legend = ui.Panel({ style:{ position:'bottom-left', padding:'8px 15px' } });
legend.add(ui.Label({ value:'LULC Classes', style:{ fontWeight:'bold', fontSize:'14px' } }));

var classes = ['Water','Forest','Cropland','Urban / Built-up','Grassland'];
classes.forEach(function(name, i) {
  var row = ui.Panel([
    ui.Label({ style:{ backgroundColor: palette[i], padding:'8px', margin:'0 0 4px 0' } }),
    ui.Label({ value: name, style:{ margin:'0 0 4px 6px' } })
  ], ui.Panel.Layout.Flow('horizontal'));
  legend.add(row);
});
Map.add(legend);

// ── 10. AREA STATISTICS ──────────────────────────────────────
var areaImage = ee.Image.pixelArea().addBands(classified);
var areas = areaImage.reduceRegion({
  reducer  : ee.Reducer.sum().group({ groupField:1, groupName:'class' }),
  geometry : roi,
  scale    : 100,
  maxPixels: 1e13
});
print('Area per class (m²)', areas);

// ── 11. EXPORT ───────────────────────────────────────────────
Export.image.toDrive({
  image       : classified,
  description : 'LULC_Classification_2023',
  folder      : 'GEE_Exports',
  fileNamePrefix: 'lulc_2023',
  region      : roi,
  scale       : 10,
  crs         : 'EPSG:4326',
  maxPixels   : 1e13
});
