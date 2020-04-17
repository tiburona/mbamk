/*
 * Main Javascript file for cookiecutter_mbam.
 *
 * This file bundles all of your javascript together using webpack.
 */

// JavaScript modules
window.$ = window.jQuery = require('jquery');
require('jquery');
require('jquery-validation');
require('font-awesome-webpack');
require('popper.js');
require('bootstrap');
require('bootstrap-fileinput');
require('bootstrap-fileinput/themes/fa/theme');
require('daikon');
require('file-saver');

// Your own code
require('./plugins.js');
require('./script.js');
//require('./papaya.js');
require('./upload.js');

//require('./FileSaver.min.js');
//require('./jszip.min.js');
//require('./jquery.validate.min.js');
