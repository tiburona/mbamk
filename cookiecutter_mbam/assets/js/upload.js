// Imports
import Filters from './filters';
var JSZip = require('jszip');
var daikon = require('daikon');
import saveAs from 'file-saver';
// jquery validate to carry out validation in modal forms
//const jquery-validation = require('jquery-validation');
require('jquery-validation/dist/jquery.validate.js');
// define(["jquery", "jquery.validate"], function( $ ) {
//     $("form").validate();
// });

// define global variables
window.uploadKeys = []; // This will hold the list of keys for thumbnais (user-selected) that will be uploaded to the site
window.pb = 0; // integer to construct progress bar as files in a CD/folder are scanned
window.files_index = [ [] ]; // this will hold the index of ordered T1 series relative to the all files on the CD/folder
window.daikon = daikon || {};
window.series_list = [ new daikon.Series() ]; // create list of all the T1 series found on the CD
window.dT = new DataTransfer(); // specs compliant (as of March 2018 only Chrome)
window.filename_list=[]; // list to hold the filenames displayed in the final upload button

// jquery functions
$(".btn").mouseup(function(){
    $(this).blur();
})

$( "#upload-toggle" ).click(function(){
    var form = $( "#uploadForm" );
    form.validate();
    console.log(form.valid())
    if (form.valid()) {
        $('#finalSubmitDialog').modal('hide');
        $('#uploadWaitDialog').modal({backdrop: 'static', keyboard: false});
    }
});

// Add form validators for the final submit form using jquery-validate (imported at top) to validate date format
$("#uploadForm").validate({
    rules: {
        date: {
            required: true,
            minlength: 10,
            maxlength: 10
        },
        action: "required",
        scan_file: {
            required: true
        },
        action: "required"
    },
    messages: {
        date: {
            required: "Please enter a valid date",
            minlength: "Your date string should have 10 characters",
            maxlength: "Your date string should have 10 characters"
        },
        action: "Please enter a valid date.",
        scan_file: {
            required: "Please select a file to upload"
        },
        action: "Please choose a file."
    }
});

// add Twitter Bootstrap progress bar function (pb is initialized as 0). pb is integer keeping track of # of files selected
export function makeProgress(numFiles, pb) {
    $(".progress-bar").css("width", pb + "%").text(Number((pb).toFixed(0)) + " %");
}

// Define the function that will add parsed image to global series_list variable if it is a structural T1-weighted MRI
// Input arguments are the file instance and its index
export function findT1(file, index) {
    // This will add a file/image to global series variable defined above if it is a T1 structural
    var reader = new FileReader()
    reader.onload = function(e) {
        let buf = e.target.result;

        // parse DICOM file
        var image = daikon.Series.parseImage(new DataView(buf));

        if (image !== null && image !== undefined && image.hasPixelData()) {
            // Here can include checks for structural terms

            if (image.getSeriesDescription().includes('T1') || image.getSeriesId().includes('T1') ||
                image.getSeriesDescription().includes('SPGR') || image.getSeriesId().includes('SPGR')) {
                console.log("Found T1 or SPGR!")
                // variable to keep track of whether a match is found with another series
                var matched = false;
                // iterate over all the series currently in the series_list
                for (var i = 0; i < series_list.length; i++) {

                    console.log("On series: " + i.toString())
                    // if it's part of the same series, add it
                    if (matched === false && (series_list[i].images.length === 0 || image.getSeriesDescription() === series_list[i].images[0].getSeriesDescription())) {
                        console.log("Added image to the initial series")
                        series_list[i].addImage(image);
                        console.log("Adding below index to the files_index array: ")
                        console.log(index)
                        files_index[i].push(index);
                        matched = true;
                        // Break out of the for loop once an image is assigned to a series
                        break;
                    // Check to see if it matches a SeriesId from another series
                    } else if (matched === false && image.getSeriesDescription() !== series_list[i].images[0].getSeriesDescription()) {

                        for (var j = 0; j < series_list.length; j++) {
                            if (j != i && image.getSeriesDescription() === series_list[j].images[0].getSeriesDescription()) {
                                console.log("Added image to different series")
                                series_list[j].addImage(image);
                                files_index[j].push(index);
                                matched = true;
                                break;
                                // If not a match continue
                            } else if (j != i && image.getSeriesDescription() !== series_list[j].images[0].getSeriesDescription()) {
                                console.log("Not a match, continuing")
                                continue;
                                // If on same series as original loop just skip it
                            } else if (j == i) {
                                continue;
                                console.log("passing")
                            }
                        }

                        // Check if a match was found. If not, then create new series to hold the image
                        if (matched === false) {
                            console.log("No match found, creating new series")
                            series_list.push(new daikon.Series());
                            console.log("Creating new file index list")
                            files_index.push([]);
                            series_list[series_list.length - 1].addImage(image);
                            files_index[files_index.length - 1].push(index)
                            break;
                        }
                    }
                }
            }
        }
    }
    // Now trigger the above function on each file of the array
    reader.readAsArrayBuffer(file);
}

export function createThumbnailUri(series) {
    series.buildSeries();
    // determine middle frame, and extract pixel data and array size etc.
    var middleSlice = Math.floor(series.images.length / 2);
    // obj.data is Float32Array (handles byte order, datatype, scale, mask)
    var obj = series.images[middleSlice].getInterpretedData(false, true);
    var width = obj.numCols;
    var height = obj.numRows;
    // get name of series
    var name = series.images[middleSlice].getSeriesDescription();
    // get number of frames (slices) and the size in bytes
    var numSlices = series.images.length;
    var size = series.images[middleSlice].getPixelDataBytes().byteLength * numSlices;

    //here scale the values so there is enough contrast in the images. later can play with how
    // the normalize factor (here set to 450 for now) can be set
    var scaleFactor = 450 / obj.max
    for (var i=0; i<obj.data.length; i+=1) {
        obj.data[i] = scaleFactor * obj.data[i]
    }

    // Create array view
    var array = new Uint8ClampedArray(obj.data);
    console.log("length of array data is: " + array.length)

    // Create original context from canvas. Use the Filters javascript object and methods defined in custom.js
    var c = Filters.getCanvas(width/2, height/2)
    var ctx = c.getContext("2d");

    //create second context from canvas to try the scaling and brightness adjustment
    var c2 = Filters.getCanvas(width, height)// width and height should be 256
    var ctx2 = c2.getContext("2d")

    // Create ImageData object
    var imgData = ctx.createImageData(width, height); // width x height
    var data = imgData.data;
    console.log("length of data is: " + data.byteLength)

    // updating alpha (from http://www.studyjs.com/html5/dicom.html)
    for (var i = 3, k = 0; i < data.byteLength; i = i + 4, k = k + 2) {
        //convert 16-bit to 8-bit, because we cannot render a 16-bit value to the canvas.
        var result = ((array[k + 1] & 0xFF) << 8) | (array[k] & 0xFF);
        result = (result & 0xFFFF) >> 8;
        data[i] = 255 - result;
    }

    // now we can draw our imagedata onto the original canvas
    ctx.putImageData(imgData, 0, 0);

    // redraw original canvas onto the new context in order to apply
    // scale and brightness filter
    ctx2.scale(2,2);
    ctx2.drawImage(ctx.canvas,0,0);

    // Grab the base64 encoded data
    const imageUri = c2.toDataURL();
    return {
        imageUri: imageUri,
        numSlices: numSlices,
        size: size,
        name: name
    }
}

var inputFileConfig = { hideThumbnailContent: true, showPreview: false, msgPlaceholder: "Select file...", dropZoneEnabled: false, msgSelected: "Selected a file.",
    browseLabel: "Browse ...", browseIcon: "<i class=\"fa fa-file\" aria-hidden=\"true\"></i>", elErrorContainer: "#errorBlock-file", showRemove: true, showUpload: false,
    maxFileCount: 3, allowedFileExtensions: ['nii','zip','nii.gz']
}

var inputCDStep1Config = { hideThumbnailContent: false, showPreview: false, maxFileCount: 2000, msgPlaceholder: "Select CD Drive or folder...", dropZoneEnabled: false, msgSelected: "Found {n} files.",
    browseLabel: "Browse ...", browseIcon: "<i class=\"fa fa-folder-open\"></i>", elErrorContainer: "#errorBlock-cd", showRemove: true, showUpload: false, minFileSize: null
}

// This button is the "Select" button along the botton of each thumbnail that is presented, note the tag/token {dataKey}
var selectBtn = '<button type="button" class="kv-cust-btn btn btn-kv btn-outline-info" onclick="this.blur();" title="Select"{dataKey}><i class="glyphicon glyphicon-upload"></i></i> Select</button>';

//Here can use InitialPreview the thumbnails created from step 1. For some reason need to have "showZoom" = true this for the custom action "Select" button to show
// After scanning the CD/folder the initialPreview and initialPreviewConfig keys will be updated with thumbnails of the scans for users to select
var inputCDStep2Config = { showPreview: true, showCaption: false, showBrowse: false, showClose: false, dropZoneEnabled: false, msgSelected: "Found {n} structural MRI scans.", overwriteInitial: false, showRemove: false,
    showUpload: false, otherActionButtons: selectBtn, fileActionSettings: { showRemove: false, showUpload: true, showDownload: false, showZoom: true, showDrag: false, }, initialPreview: [],
    initialPreviewAsData: false, initialPreviewConfig: [], theme: "fa" }

var sampleImagesConfig = { showPreview: true, showCaption: false, showBrowse: false, showClose: false, dropZoneEnabled: false, overwriteInitial: false, showRemove: false,
    showUpload: false, fileActionSettings: { showRemove: false, showUpload: false, showDownload: false, showZoom: false, showDrag: false, }, initialPreview: [],
    initialPreviewAsData: false, initialPreviewConfig: [] }

// initialize file input with defaults and specify what happens when a file is loaded
$("#input-file").fileinput(inputFileConfig).on('filebatchselected', function(event, files) {
    // on("fileloaded", function(event, file, previewId, index, reader) {
    // const dT = new ClipboardEvent('').clipboardData //|| // Firefox < 62 workaround exploiting https://bugzilla.mozilla.org/show_bug.cgi?id=1422655
    // new DataTransfer(); // specs compliant (as of March 2018 only Chrome)
    // check out https://stackoverflow.com/questions/47119426/how-to-set-file-objects-and-length-property-at-filelist-object-where-the-files-a
    // transfer the file input to the final submit form

    try {
        var dT = new DataTransfer(); // specs compliant (as of March 2018 only Chrome)
        filename_list=[];
        for (var i = 0; i < files.length; i++) {
            dT.items.add(new File([ files[i] ], files[i].name ));
            filename_list.push(files[i].name)
        }
        scan_file.files = dT.files;

        // Below just adds the name of the file to the finalSubmit Form
        $("#upload-toggle").text("Upload: " + filename_list.join(', '));
    } catch(e) {
        // Here just let the user download the file and direct them to the 'legacy' upload form
        alert('Please upload the file using the following form instead, or, try using Chrome browser.')
        window.location.replace(Flask.url_for('scan.add_experiment_and_scans', { "action": "old" } ));
    }

    // Show the finalSubmit dialog
    $("#go-back").hide();
    $("#finalSubmitDialog").modal('show');
});

// Below will set what the Reset button does in the finSubmit and compareScans Dialog
$('.start-over').on("click", function() {
    // check if the below modals are currently shown, if so then hide them.
//($("element").data('bs.modal') || {})._isShown
    if (($('#finalSubmitDialog').data('bs.modal') || {_isShown: false})._isShown) {
        $('#finalSubmitDialog').modal('hide');
    }

    if (($('#compareScanDialog').data('bs.modal') || {_isShown: false})._isShown) {
        $('#compareScanDialog').modal('hide');
        $("#input-cd-step2").fileinput('clear');
    }

    if (($('#pleaseWaitDialog').data('bs.modal') || {_isShown: false})._isShown) {
        console.log("cancel on progress modal pressed")
        $('#pleaseWaitDialog').modal('hide');
        $('#input-cd-step1').fileinput('reset');
    }

    // Below to make sure the background is removed when modal is closed (sometimes it was buggy)
    $('body').removeClass('modal-open');
    $('.modal-backdrop').remove();

    $('#input-cd-step1').fileinput('clear');
    $('#input-file').fileinput('clear')

    // Clear out the scan date just in case too
    $("#date").val("")

});

// Below button is to return to the compareScans Dialog from the finalSubmit page
$('#go-back').on("click", function() {
    console.log("clicked go back")
    $('#finalSubmitDialog').modal('hide')
    $('#compareScanDialog').modal('show')
})

// initialize CD drive input with defaults (step 1 for selecting the CD Drive/folder)
$("#input-cd-step1").fileinput( inputCDStep1Config ).on('change', function(event) {
    // initialize global variables each time user clicks Browse button without refreshing
    window.files_index=[ [] ];
    window.series_list = [ new daikon.Series() ];
    window.uploadKeys = [];
    window.filename_list=[];

   // Reset global pb variable
    pb = 0;
    // below to time how long it takes to scan the files
    console.time('time_to_scan');

    // set next button in the compareScans Dialog to disabled
    $("#next-button").prop('disabled',true)

    // trigger the progress bar modal after user selects CD drive/folder
    $('#pleaseWaitDialog').modal({backdrop: 'static', keyboard: false});
}).on('fileselect', function(event, numFiles, label) {
    // increment the progress bar as each file from the folder is selected
    if (pb == 0) {
        pb = 100 / numFiles;
    } else if (pb < 100) {
        pb =  pb + 100 / numFiles;
    }
    makeProgress(numFiles,pb);
}).on("fileloaded", function(event, file, previewId, index, reader) {
    // Test whether the file has "T1" or "SPGR" in the dicom headers, if so, add image to the global daikon series list
    findT1(file, index);
}).on('filebatchselected', function(event, files) {
    console.log("Time to scan " + files.length.toString() + " files ")
    console.timeEnd("time_to_scan")

    // First filter out series that are fewer than X slices etc.
    var min_images = 10;
    for (var i = series_list.length - 1; i >= 0; i--) {
        if (series_list[i].images.length < min_images) {
            series_list.splice(i, 1);
        }
    }

    // Below lists to hold the imageUris for each series found and the sample images to go along with them
    var initPreviewList = [];
    var initPreviewConfigList = [];
    var sampleImagesList = [];
    var sampleImagesConfigList = [];

    // Check whether the series has add images added to it. If not, alert the user that no structurals were found on the CD.
    if (series_list.length > 0) {
        // iterate over each series, draw and create thumbnails to show users at next step
        for (var j = 0; j < series_list.length; j++) {
            // order the image files, determines number of frames, etc.
            var series = series_list[j];

            // create thumbNail object with information required to display the thumbnails
            var thumbNail = createThumbnailUri(series)

            // Here add the imageUris to the lists for the compareScansDialog
            initPreviewList.push("<img src='" + thumbNail.imageUri + "' class='kv-preview-data file-preview-image'>")
            initPreviewConfigList.push({ caption: thumbNail.name + " (" + thumbNail.numSlices + " slices)", url: thumbNail.imageUri, size: thumbNail.size, key: j })

            // Here add the sample images to show based on the orientations of the T1 images
            // Get orientation: 0 is sagital, 1 is Coronal, 2 is axial, 3 is Oblique, -2 is unknown
            // AXIAL_SAMPLE, COR_SAMPLE, and SAG_SAMPLE are defined in script tag in layout.html in order to
            // use asset_url_for from flask-webpack.
            switch ( series.images[0].getAcquiredSliceDirection() ) {
                case 2:
                    console.log("add axial sample image")
                    var img = "<img src='" + $AXIAL_SAMPLE + "' class='kv-preview-data file-preview-image'/>";

                    if (sampleImagesList.includes( img ) == false) {
                        sampleImagesList.push( img );
                        sampleImagesConfigList.push({ caption: 'Axial T1', url: $AXIAL_SAMPLE})
                    }
                    break;
                case 1:
                    console.log("add coronal sample image")
                    var img = "<img src='" + $COR_SAMPLE + "' class='kv-preview-data file-preview-image'/>";
                    if (sampleImagesList.includes( img ) == false) {
                        sampleImagesList.push( img );
                        sampleImagesConfigList.push({ caption: 'Coronal T1', url: $COR_SAMPLE })
                    }
                    break;
                case 0:
                    console.log("add sagittal sample image")
                    var img = "<img src='" + $SAG_SAMPLE + "' class='kv-preview-data file-preview-image'/>";
                    if (sampleImagesList.includes( img ) == false) {
                        sampleImagesList.push( img );
                        sampleImagesConfigList.push({ caption: 'Sagittal T1', url: $SAG_SAMPLE })
                    }
                    break;
                case 3:
                    // come back to
                    break;
                case -1:
                    // come back to
                    break;
            }

        // End of series_list for loop
        }

        // Here update the preview to show thumbnails of the structural MRI files
        inputCDStep2Config[ 'initialPreview' ] = initPreviewList;
        inputCDStep2Config[ 'initialPreviewConfig' ] = initPreviewConfigList;

        // Here add the sample images gallery with thumbnails using the lists generated in previous for loop
        sampleImagesConfig[ 'initialPreview' ] = sampleImagesList;
        sampleImagesConfig[ 'initialPreviewConfig' ] = sampleImagesConfigList;

        // initialize thumbnail and upload step (step 2 for selecting thumbnail and uploading etc. to be shown on cd-modal-#2)
        $("#input-cd-step2").fileinput('destroy').fileinput( inputCDStep2Config );
        $("#sample-images").fileinput('destroy').fileinput( sampleImagesConfig );

        // The below will add the key for each thumbnail selected by user to the set of all keys to upload
        $('.kv-cust-btn').on("click", function() {
            // extract the key (which corresponds to order of thumbnails) to know which series to select
            var $btn = $(this), key = $btn.data('key');

            // add the key to the uploadKeys list
            $(this).toggleClass("active");
            // either push or splice key depending on active status of button
            if ($(this).hasClass("active")) {
                uploadKeys.push(key)
                filename_list.push(series_list[key].images[0].getSeriesDescription() + ".zip")
            } else {
                var idx = uploadKeys.indexOf(key)
                if (idx > -1) {
                    uploadKeys.splice(idx,1);
                    filename_list.splice(idx,1);
                }

            }

            // Here disable next-button if no upload keys seleted, or enable if at least one is
            if (uploadKeys.length == 0) {
                $("#next-button").prop('disabled',true)
            } else {
                $("#next-button").prop('disabled',false)
            }

        });

        $('#next-button').on("click", function() {
            // re-initialize globals
            dT = new DataTransfer();

            // for each key, zip up series and add to the above datatransfer object
            for (var i = 0; i < uploadKeys.length; i++) {
                var key = uploadKeys[i];
                var series = series_list[key];
                //var download = $(this).hasClass('download-button') // determine if the download button was pressed
                //var name = series.images[0].getSeriesDescription()
                console.log("Name of series is: " + filename_list[i])
                // Here access the indeces of the series images after they get reordered by BuildSeries() and
                // reorder the files_index to reflect this order
                var series_idx = series.getOrder();

                console.log("on Key #: ")
                console.log(key);
                console.log("Order of the files before sorting according to BuildSeries:")
                console.log(files_index[key])

                // Sort array according to map function. https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort
                // temporary array holds objects with position and sort-value
                var mapped = files_index[key].map(function(el, j) {
                    return { index: j, value: el };
                });

                // sorting the mapped array containing the reduced values
                mapped.sort(function(a, b) {
                    if (a.value > b.value) {
                        return 1;
                    }
                    if (a.value < b.value) {
                        return -1;
                    }
                    return 0;
                });

                // container for the resulting order
                var result = mapped.map(function(el) {
                    return files_index[key][el.index];
                });

                console.log("Order of the files after sorting according to BuildSeries:")
                console.log(result)

                // Here create a zip of the select set of dicoms
                var zip = new JSZip();
                // Add the files that are included as part of the series (hopefully in right order)
                try {
                    for (var k = 0; k < files_index[key].length; k++) {
                        var f = files[files_index[key][k]];
                            console.log("adding dicom file to the zip file")
                            console.log(f)
                            zip.file(f.name, f);
                        }
                } catch(e) {
                    $("#errorMsgDialog").modal("show");
                    break;
                }

                // Now convert zip to blob and pass to upload form or download the zipped file
                zip.generateAsync({
                    type:"blob",
                    mimeType: "application/zip",
                }).then(function (blob) { // 1) generate the zip file
                    try {
                        console.log("adding zip file to dT object")
                        console.log(filename_list)
                        // Here if can pass the selected file onto the for
                        dT.items.add(new File([ blob ], filename_list[i] + ".zip" ));
                    } catch(e) {
                        // Here just let the user download the file and direct them to the 'legacy' upload form
                        alert('Press OK to download the file to your computer. You will be redirected to a brief upload form. Choose the downloaded file under the "Image" field of the form.')
                        saveAs(blob, filename_list[i] + ".zip"); // 2) trigger the download

                        // redirect to the "legacy" file upload form in future. Maybe can add new type of action for that
                    } finally {
                        // execute on the last for loop
                        console.log("On index: ")
                        console.log(i)
                        // Here run stuff on the last leg of for loop
                        if (i == uploadKeys.length) {
                            console.log("OK in last leg of loop")
                            // here try to grab the scan date from the dicom file
                            var studyDate = series.images[0].getStudyDate();
                            if (studyDate) {
                                console.log("Ok grabbed date")
                                var day = ("0" + studyDate.getDate()).slice(-2);
                                var month = ("0" + (studyDate.getMonth() + 1)).slice(-2);
                                var ScanDate = studyDate.getFullYear()+"-"+(month)+"-"+(day);
                                $('#date').val(ScanDate); // this will add the date value to the modal new upload form
                                console.log(ScanDate)
                            }

                            try {
                                console.log("filename list here is: ")
                                console.log(filename_list)
                                $("#upload-toggle").text("Upload: " + filename_list.join(', '));
                                scan_file.files = dT.files;
                                //$('#scan_date').val(ScanDate); // this will add the date value to the modal new upload form

                                // show the compare thumbnails
                                $('#compareScanDialog').modal('hide');
                                $('#finalSubmitDialog').modal('show');
                            } catch(e) {
                                console.log("Need to use old form")
                                if (ScanDate) {
                                    //var uri = "/scans/add_experiment_and_scans?action=old&date=" + ScanDate
                                    //window.location.replace(Flask.url_for("scan.add_experiment_and_scans", {"action": "old", "date": ScanDate} ));
                                } else {
                                    //window.location.replace("{{ url_for('scan.add_experiment_and_scans', action='old') }}")
                                    //window.location.replace(Flask.url_for("scan.add_experiment_and_scans", {"action": "old"} ))
                                }
                            }
                        }
                    }
                });

            // end of for loop for going through all keys
            }
        });

        // hide the progress bar
        $('#pleaseWaitDialog').modal('hide')

        // show the compare thumbnails
        $("#go-back").show();
        $('#compareScanDialog').modal({backdrop: 'static', keyboard: false})
    } else {
        // Here handle the case where no matching dicoms are found
        alert("Did not find any structural MRI dicom series with more than 10 slices")
    }
});
