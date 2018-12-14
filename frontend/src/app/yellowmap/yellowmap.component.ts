import {Component, OnInit} from '@angular/core';

import OlMap from 'ol/Map';
import OlXYZ from 'ol/source/XYZ';
import OlTileLayer from 'ol/layer/Tile';
import OlView from 'ol/View';
import Feature from 'ol/Feature';
import Point from 'ol/geom/Point';
import {Vector as VectorLayer} from 'ol/layer';
import VectorSource from 'ol/source/Vector';
import {fromLonLat, transformExtent} from 'ol/proj';
import {Circle as CircleStyle, Fill, Icon, Stroke, Style} from 'ol/style';
import OSMXML from 'ol/format/OSMXML';
import {bbox as bboxStrategy} from 'ol/loadingstrategy.js';

@Component({
  selector: 'app-yellowmap',
  templateUrl: './yellowmap.component.html',
  styleUrls: ['./yellowmap.component.scss']
})
export class YellowmapComponent implements OnInit {
  map: OlMap;
  source: OlXYZ;
  layer: OlTileLayer;
  view: OlView;

  constructor() {
  }

  ngOnInit() {
    this.source = new OlXYZ({
      url: '//tile.osm.org/{z}/{x}/{y}.png'
    });

    this.layer = new OlTileLayer({
      source: this.source
    });

    this.view = new OlView({
      center: fromLonLat([15.4395, 47.0707]),
      zoom: 16
    });

    const styles = {
      'icon': new Style({
        image: new CircleStyle({
          radius: 7,
          fill: new Fill({color: 'rgba(255, 211, 3, 0.7)'}),
          stroke: new Stroke({
            color: 'rgba(0,0,0,1)', width: 2.5
          })
        })
      })
    };

    const that = this;
    const vectorSource = new VectorSource({
      format: new OSMXML(),
      loader: function (extent, resolution, projection) {
        const epsg4326Extent = transformExtent(extent, projection, 'EPSG:4326');
        const client = new XMLHttpRequest();
        client.open('POST', '//overpass-api.de/api/interpreter');
        client.addEventListener('load', function () {
          const features = new OSMXML().readFeatures(client.responseText, {
            featureProjection: that.map.getView().getProjection()
          });
          vectorSource.addFeatures(features);
        });
        const boundingBox = '(' + epsg4326Extent[1] + ',' + epsg4326Extent[0] + ',' + epsg4326Extent[3] + ',' + epsg4326Extent[2] + ')';
        const query = '(node["amenity"="restaurant"]' + boundingBox + ';);out meta;';
        client.send(query);
      },
      strategy: bboxStrategy
    });

    const pharmacyLayer = new VectorLayer({
      source: vectorSource,
      style: function (feature) {
        return styles['icon'];
      }
    });


    this.map = new OlMap({
      target: 'map',
      layers: [
        this.layer,
        pharmacyLayer
      ],
      view: this.view
    });
  }
}
