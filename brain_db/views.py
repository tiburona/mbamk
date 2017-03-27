from flask_brain_db import app, settings
from flask import render_template, redirect, flash, url_for, session, abort, request
from brain_db.form import SetupForm, ScanForm #CommentForm
from flask_brain_db import db, uploaded_images
from user.models import User
from brain_db.models import Scan
from user.decorators import login_required, owner_required, set_vars
from slugify import slugify
import os, pyxnat, bcrypt, time, json, collections
from helper.database_count import get_db_counts

# Fix this to not rely on absolute path
# central = pyxnat.Interface(config='~/workspace/flask_brain_db/central.cfg')
#central = pyxnat.Interface(config=url_for('static', filename='central.cfg'))
xnat = pyxnat.Interface(config="mind-xnat.cfg")
#xnat = pyxnat.Interface(config='/home/ubuntu/workspace/flask_brain_db/static/central.cfg')
PROJECT='MBAM_TEST'
USER='mbam'
PSWD='mbam123'
XNAT_URL='mind-xnat.nyspi.org'
bdir=settings.UPLOADED_IMAGES_DEST 
url_bdir=settings.UPLOADED_IMAGES_URL 

SCANS_PER_PAGE = 10

@app.route('/')
@app.route('/index')
def index():
    if session['logged_in']:
        user_id=session['user_id']
        scan=Scan.query.filter_by(user_id=user_id).first()
        # Here assign value to session indicating whether user has uploaded scan or not
        if scan:
            session['scan_uploaded']=True
        else:
            session['scan_uploaded']=None
        counts=None
    else:
        print "ok here"
        counts = get_db_counts()
        scan=None
    return render_template('brain_db/index.html', scan=scan,counts=counts)
 
@app.route('/admin')
@app.route('/admin/<int:page>')
@owner_required
def admin(page=1):
    if session.get('is_author'):
        scans = Scan.query.order_by(Scan.publish_date.desc()).paginate(page, SCANS_PER_PAGE, False)
        return render_template('brain_db/admin.html', scans=scans)
    else:
        abort(403)

@app.route('/edit', methods=('GET','POST'))
@login_required
def edit():
    user_id=session['user_id']
    scan=Scan.query.filter_by(user_id=user_id).first_or_404()
    form = ScanForm(obj=scan)

    if form.validate_on_submit():
        original_image = scan.uploaded_file
        form.populate_obj(scan) # just to change whatever has been changed in the form
        if form.uploaded_file.has_file():
            image = request.files.get('uploaded_file')
            try:
                filename = uploaded_images.save(image)
            except:
                flash("The image was not uploaded")

            if filename:
                scan.uploaded_file = filename
                
        else:
            scan.uploaded_file = original_image

        time.sleep(15)
        return redirect(url_for('raw_view')) 
        
    return render_template('brain_db/upload.html', form=form, scan=scan, action="edit") # changed post

# 
# @app.route('/upload/<string:edit>', methods=('GET','POST')) # changed post to upload
# @login_required
# def upload():
#     user_id=session['user_id']
#     scan=Scan.query.filter_by(user_id=user_id).first_or_404()
#     form = ScanForm(obj=scan)
    
#     form = ScanForm()
#     if form.validate_on_submit():
#         image = request.files.get('uploaded_file')
#         scan_number = request.values.get('scan_number')
#         filename = None
#         try:
#             # Here set the subfolder to save images to 
#             SUBJECT=str(session["user_id"]).zfill(4)
#             EXPERIMENT=SUBJECT + "_MR" + str(scan_number)
#             folder = 'data/' + SUBJECT + '/' + EXPERIMENT 
#             filename = uploaded_images.save(image,folder)
#         except:
#             flash("The image was not uploaded")

#         #brain_db = Brain_db.query.first() # Assuming only one brain_db for now
#         user = User.query.filter_by(username=session['username']).first() # Will have to fix this to query by user id!! Unless enforcing unique usernames
#         title = form.title.data
#         scan_age = form.scan_age.data
#         scan_date = form.scan_date.data
#         #slug = slugify(title)
#         file_base, file_extension = os.path.splitext(filename)
        
#         # Here add the scan to XNAT and get the unique id for the scan and include that 
#         # in the local database. For now use TEST_MIND for development purposes
#         # later can put this in it's own module
#         SUBJECT=str(user.id).zfill(4)
#         EXPERIMENT="%s_MR%s" % (str(user.id).zfill(4),str(scan_number))
#         FILE=uploaded_images.path(file_base)
        
#         proj_obj=xnat.select.project(PROJECT)
#         sub_obj=proj_obj.subject(SUBJECT) # Zero pad the number to four digits
#         if not sub_obj.exists():
#             sub_obj.insert()
        
#         exp_obj=sub_obj.experiment(EXPERIMENT) 
#         # Delete the previous scans if they already exist
#         if exp_obj.exists():
#             allScans=exp_obj.scans()
#             for scan in allScans:
#                 SCAN = scan.attrs.get('ID')
#                 print "deleting scan " + SCAN
#                 cmd="""curl -X DELETE -u {}:{} 'https://{}/data/projects/{}/subjects/{}/experiments/{}/scans/{}?inbody=true'""".format(USER,PSWD,XNAT_URL,PROJECT,SUBJECT,EXPERIMENT,SCAN)
#                 os.system(cmd)
#         else:   
#             exp_obj.create()
        
#         #Here set age and sex in XNAT 
#         # must get from the User object
#         sub_obj.attrs.set('xnat:subjectData/demographics[@xsi:type=xnat:demographicData]/gender',user.sex)
#         if scan_age:
#             sub_obj.attrs.set('xnat:subjectData/demographics[@xsi:type=xnat:demographicData]/age',scan_age)
#         else: 
#             # here write other ways to estimate age if not provided 
#             sub_obj.attrs.set('xnat:subjectData/demographics[@xsi:type=xnat:demographicData]/age',scan_age)
        
#         # Now insert the scan
#         print "OK about to upload to xnat: " + uploaded_images.path(filename)
#         if file_extension == ".nii":
#             exp_obj.scan('T1').resource('NIFTI').file(file_base).insert(
#             uploaded_images.path(file_base),
#             content='T1',
#             overwrite=True,
#             type='T1',  # May need to change this to SPGR, MPRAGE, FLAIR etc?
#             format='NIFTI')
#         elif file_extension == ".zip":
#             # The below posts .zip to the prearchive and lets xnat expand DICOM and put in archive
#             cmd="""curl -X POST -u {}:{} --data-binary @{}.zip -H 'Content-Type: application/zip' 'https://{}/data/services/import?project={}&subject={}&session={}&overwrite=delete&prearchive=true&inbody=true'""".format(USER,PSWD,FILE,XNAT_URL,PROJECT,SUBJECT,EXPERIMENT)
#             os.system(cmd)
#             # The below gives more control or naming the scan (had troubling changing scan ID with above method)
#             # First create the scan
#             #cmd="""curl -X PUT -u {}:{} 'https://{}/data/projects/{}/subjects/{}/experiments/{}/scans/{}?xsiType=xnat:mrScanData'""".format(USER,PSWD,XNAT_URL,PROJECT,SUBJECT,EXPERIMENT,SCAN)
#             # Now upload the scan
#             #cmd="""curl -X PUT -u {}:{} 'https://{}/data/projects/{}/subjects/{}/experiments/{}/scans/{}/resources/DICOM/files/results.dcm?extract=true&format=DICOM&content=T1_RAW' -F 'file=@{}.zip'""".format(USER,PSWD,XNAT_URL,PROJECT,SUBJECT,EXPERIMENT,SCAN,FILE)
#             #print cmd
#             #os.system(cmd)
            
#         # here get the XNAT accession ID
#         constraints = [('xnat:subjectData/PROJECT','=',PROJECT),
#                 'AND',
#         ('xnat:subjectData/label','=',SUBJECT)]
#         xnatSubjectID = xnat.select('xnat:subjectData',['xnat:subjectData/SUBJECT_ID']).where(constraints)
#         #xnatSubjectID is a JsonTable object
#         xnat_subject_id = xnatSubjectID['subject_id']
      
#         #expObj =xnat.select.project(project_label).subject(xnat_subject_id).experiment(session_label)
#         xnat_session_id = exp_obj.attrs.mget(['ID'])
        
#         # xnat_accession is subject specific. Later will have to figure out how 
#         # to deal with multiple scans from same subject
#         # Try to retrieve scan for the user. If it doesn't exist, create scan and add to the local mysql database.
#         # if it does exist, then update the info. This way only one scan exists for each subject. In FUTURE change download location
#         # to coincide with the XNAT download location! (i.e. raw_data folder for the zipped dicoms etc.)
#         scan = Scan.query.filter_by(user_id=user.id).first()
#         if scan: # If scan already exists for this user then just update with new form information
#             #scan = Scan(brain_db, user, xnat_subject_id, xnat_session_id, title, age, filename)
#             scan.title=title
#             scan.scan_number=scan_number
#             scan.scan_age = scan_age
#             scan.scan_date = scan_date
#             scan.uploaded_file=filename
#             scan.xnat_session_id=xnat_session_id
#             scan.xnat_subject_id=xnat_subject_id
#             db.session.commit()
#             flash("Scan updated")
#         else:
#             scan = Scan(user, xnat_subject_id, xnat_session_id, title, filename, scan_number, scan_age, scan_date)
#             db.session.add(scan)
#             db.session.commit()
#             flash("Scan added")
        
#         # here wait a few seconds to make sure the scan is uploaded to DB first
#         time.sleep(15)
#         return redirect(url_for('raw_view')) 
#         #return redirect(url_for('scan_view',scan=scan))
        
#     return render_template('brain_db/upload.html', form=form, action="new") #changed post to upload

@app.route('/upload', methods=('GET','POST')) # changed post to upload
@login_required
def upload():
    user_id=session['user_id']
    form = ScanForm()
    if form.validate_on_submit():
        image = request.files.get('uploaded_file')
        scan_number = request.values.get('scan_number')
        filename = None
        try:
            # Here set the subfolder to save images to 
            SUBJECT=str(session["user_id"]).zfill(4)
            EXPERIMENT=SUBJECT + "_MR" + str(scan_number)
            folder = 'data/' + SUBJECT + '/' + EXPERIMENT 
            filename = uploaded_images.save(image,folder)
        except:
            flash("The image was not uploaded")

        #brain_db = Brain_db.query.first() # Assuming only one brain_db for now
        user = User.query.filter_by(username=session['username']).first() # Will have to fix this to query by user id!! Unless enforcing unique usernames
        title = form.title.data
        scan_age = form.scan_age.data
        scan_date = form.scan_date.data
        #slug = slugify(title)
        file_base, file_extension = os.path.splitext(filename)
        
        # Here add the scan to XNAT and get the unique id for the scan and include that 
        # in the local database. For now use TEST_MIND for development purposes
        # later can put this in it's own module
        SUBJECT=str(user.id).zfill(4)
        EXPERIMENT="%s_MR%s" % (str(user.id).zfill(4),str(scan_number))
        FILE=uploaded_images.path(file_base)
        
        proj_obj=xnat.select.project(PROJECT)
        sub_obj=proj_obj.subject(SUBJECT) # Zero pad the number to four digits
        if not sub_obj.exists():
            sub_obj.insert()
        
        exp_obj=sub_obj.experiment(EXPERIMENT) 
        
        # Delete the previous scans if they already  on XNAT and locally
        if exp_obj.exists():
            allScans=exp_obj.scans()
            for scan in allScans:
                SCAN = scan.attrs.get('ID')
                print "deleting scan " + SCAN
                cmd="""curl -X DELETE -u {}:{} 'https://{}/data/projects/{}/subjects/{}/experiments/{}/scans/{}?inbody=true'""".format(USER,PSWD,XNAT_URL,PROJECT,SUBJECT,EXPERIMENT,SCAN)
                os.system(cmd)
        else:   
            exp_obj.create()
        
        scan=Scan.query.filter_by(user_id=user_id).first()
        if scan.struct_subjectSpace:
            print "Ok deleting scan.struct_subjectSpace"
            file=app.config['BASEDIR'] + scan.struct_subjectSpace
            scan.struct_subjectSpace=None
            if os.path.isfile(file):
                print "Ok deleting scan.struct_subjectSpace file path"
                os.remove(file)
        if scan.zscore_subjectSpace:
            file = app.config['BASEDIR'] + scan.zscore_subjectSpace
            scan.zscore_subjectSpace=None
            if os.path.isfile(file):
                os.remove(file)
            
        #Here set age and sex in XNAT 
        # must get from the User object
        sub_obj.attrs.set('xnat:subjectData/demographics[@xsi:type=xnat:demographicData]/gender',user.sex)
        if scan_age:
            sub_obj.attrs.set('xnat:subjectData/demographics[@xsi:type=xnat:demographicData]/age',scan_age)
        else: 
            # here write other ways to estimate age if not provided 
            sub_obj.attrs.set('xnat:subjectData/demographics[@xsi:type=xnat:demographicData]/age',scan_age)
        
        # Now insert the scan
        print "OK about to upload to xnat: " + uploaded_images.path(filename)
        if file_extension == ".nii":
            exp_obj.scan('T1').resource('NIFTI').file(file_base).insert(
            uploaded_images.path(file_base),
            content='T1',
            overwrite=True,
            type='T1',  # May need to change this to SPGR, MPRAGE, FLAIR etc?
            format='NIFTI')
        elif file_extension == ".zip":
            # The below posts .zip to the prearchive and lets xnat expand DICOM and put in archive
            cmd="""curl -X POST -u {}:{} --data-binary @{}.zip -H 'Content-Type: application/zip' 'https://{}/data/services/import?project={}&subject={}&session={}&overwrite=delete&prearchive=true&inbody=true'""".format(USER,PSWD,FILE,XNAT_URL,PROJECT,SUBJECT,EXPERIMENT)
            os.system(cmd)
            # The below gives more control or naming the scan (had troubling changing scan ID with above method)
            # First create the scan
            #cmd="""curl -X PUT -u {}:{} 'https://{}/data/projects/{}/subjects/{}/experiments/{}/scans/{}?xsiType=xnat:mrScanData'""".format(USER,PSWD,XNAT_URL,PROJECT,SUBJECT,EXPERIMENT,SCAN)
            # Now upload the scan
            #cmd="""curl -X PUT -u {}:{} 'https://{}/data/projects/{}/subjects/{}/experiments/{}/scans/{}/resources/DICOM/files/results.dcm?extract=true&format=DICOM&content=T1_RAW' -F 'file=@{}.zip'""".format(USER,PSWD,XNAT_URL,PROJECT,SUBJECT,EXPERIMENT,SCAN,FILE)
            #print cmd
            #os.system(cmd)
            
        # here get the XNAT accession ID
        constraints = [('xnat:subjectData/PROJECT','=',PROJECT),
                'AND',
        ('xnat:subjectData/label','=',SUBJECT)]
        xnatSubjectID = xnat.select('xnat:subjectData',['xnat:subjectData/SUBJECT_ID']).where(constraints)
        #xnatSubjectID is a JsonTable object
        xnat_subject_id = xnatSubjectID['subject_id']
      
        #expObj =xnat.select.project(project_label).subject(xnat_subject_id).experiment(session_label)
        xnat_session_id = exp_obj.attrs.mget(['ID'])
        
        # xnat_accession is subject specific. Later will have to figure out how 
        # to deal with multiple scans from same subject
        # Try to retrieve scan for the user. If it doesn't exist, create scan and add to the local mysql database.
        # if it does exist, then update the info. This way only one scan exists for each subject. In FUTURE change download location
        # to coincide with the XNAT download location! (i.e. raw_data folder for the zipped dicoms etc.)
        if scan: # If scan already exists for this user then just update with new form information
            #scan = Scan(brain_db, user, xnat_subject_id, xnat_session_id, title, age, filename)
            scan.title=title
            scan.scan_number=scan_number
            scan.scan_age = scan_age
            scan.scan_date = scan_date
            scan.uploaded_file=filename
            scan.xnat_session_id=xnat_session_id
            scan.xnat_subject_id=xnat_subject_id
            print "The below should be None"
            print scan.struct_subjectSpace
            db.session.commit()
            flash("Scan updated")
        else:
            scan = Scan(user, xnat_subject_id, xnat_session_id, title, filename, scan_number, scan_age, scan_date)
            db.session.add(scan)
            db.session.commit()
            flash("Scan added")
        
        # here wait a few seconds to make sure the scan is uploaded to DB first
        return redirect(url_for('raw_view')) 
        #return redirect(url_for('scan_view',scan=scan))
        
    return render_template('brain_db/upload.html', form=form, action="new") #changed post to upload


@app.route('/raw_view')
@login_required
def raw_view():
    user_id=session['user_id']
    scan=Scan.query.filter_by(user_id=user_id).first_or_404()
    
    if not scan.struct_subjectSpace:
        print "OK HERE!!!!!!!!!!!!!!!!"
       # bdir=settings.UPLOADED_IMAGES_DEST 
    #    url_bdir=settings.UPLOADED_IMAGES_URL 
        SUBJECT=str(user_id).zfill(4)
        EXPERIMENT=SUBJECT + "_MR1"
        SCAN='*' # Need to change so can find scan by scan type
        
        # local file locations
        template_file = bdir + 'data/' + SUBJECT + '/' + EXPERIMENT + '/struct_subjectSpace.nii.gz'
        template_url  = url_bdir + 'data/' + SUBJECT + '/' + EXPERIMENT + '/struct_subjectSpace.nii.gz'
        # This is REST path on xnat database
        template_path='/projects/' + PROJECT + '/subjects/' + SUBJECT + '/experiments/' + EXPERIMENT + '/scans/' + SCAN + '/resources/NIFTI/files/scan.nii.gz'
        print template_path
        print os.path.isfile(template_file)
        os.system('mkdir --parents ' + os.path.dirname(template_file))
        
        import pyxnat
        xnat=pyxnat.Interface(config='mind-xnat.cfg')

        template_obj=xnat.select(template_path).first()
        while not template_obj.exists():
            print "Still waiting for XNAT archiving"
            time.sleep(2)
            template_obj=xnat.select(template_path).first()
        else:
            xnat.select(template_path).first().get(template_file)
            print "Downloaded new MRI"
        # verify file exists, then commit
        if os.path.isfile(template_file):
            print "OK HERE 2"
            scan.struct_subjectSpace=template_url
            db.session.commit()
            flash("Successfully downloaded struct image from XNAT")
            #xnat.select(overlay_path).get(overlay_file)

    template_url=scan.struct_subjectSpace
    template_base=os.path.basename(scan.struct_subjectSpace)
    overlay_url=None
    overlay_base=None
    title="Original MRI scan"
    Images = collections.namedtuple('Images', ['title','template_url', 'overlay_url','template_base','overlay_base'])
    img_obj=Images(title=title,template_url=template_url,template_base=template_base,overlay_url=overlay_url,overlay_base=overlay_base)

    return render_template('brain_db/scan_view.html', images=img_obj) # changed article to scan_view

@app.route('/raw_zscore_view')
@login_required
def raw_zscore_view():
    user_id=session['user_id']
    scan=Scan.query.filter_by(user_id=user_id).first_or_404()
    #url_bdir=settings.UPLOADED_IMAGES_URL
    
    if not scan.zscore_subjectSpace or not os.path.exists(url_bdir + scan.zscore_subjectSpace): # retrieve the file from XNAT if not already exist locally
        #bdir=settings.UPLOADED_IMAGES_DEST 
         
        SUBJECT=str(user_id).zfill(4)
        EXPERIMENT=SUBJECT + "_MR1"
        SCAN='*' # Need to change so can find scan by scan type
        
        # here attempt to download zscore image. If doesn't exist then run the pipeline. Maybe better
        # to put this in a separate route that is activated by subject button press after validating the raw scan
        overlay_file = bdir + 'data/' + SUBJECT + '/' + EXPERIMENT + '/zscore_subjectSpace.nii.gz'
        overlay_url  = url_bdir + 'data/' + SUBJECT + '/' + EXPERIMENT + '/zscore_subjectSpace.nii.gz'
        overlay_path='/projects/' + PROJECT + '/subjects/' + SUBJECT + '/experiments/' + EXPERIMENT + '/scans/' + SCAN + '/resources/Zscores/files/Zscore_Sub.nii.gz'
        os.system('mkdir --parents ' + os.path.dirname(overlay_file))
        #scn_obj=xnat.select(overlay_path).get(overlay_file).first()
        import pyxnat
        xnat=pyxnat.Interface(config='mind-xnat.cfg')
        scn_obj=xnat.select(overlay_path).first()
        
        # First check if file already exists locally 
        # if so then commit path to model
        if os.path.exists(overlay_file):
            scan.zscore_subjectSpace=overlay_url
            db.session.commit()
            flash("zscore image already downloaded from XNAT")
            #xnat.select(overlay_path).get(overlay_file)
        # If the zscore map exists on XNAT then download
        elif scn_obj.exists():
            xnat.select(overlay_path).first().get(overlay_file)
            scan.zscore_subjectSpace=overlay_url
            db.session.commit()
            flash("zscore image successfully downloaded from XNAT and local path committed to local DB")
        # If the file does not exist on xnat, then must run the pipeline
        elif not scn_obj.exists():
            # Here send curl action to start pipeline for VBM analysis. Will need to figure out how to do 
            # email notification to the user. Otherwise just say check back in an hour for now. 
            uri = """/data/projects/{}/pipelines/Segment_to_Zscore/experiments/{}?inbody=true""".format(PROJECT, scan.xnat_session_id)
            method='POST'
            xnat._exec(uri,method=method)
            flash("Zscore map not generated yet. Please check back in 20 minutes!")
            return redirect(url_for('raw_view'))
        else:
            flash("Error obtaining or generating zscore file")
            return redirect(url_for('raw_view')) 
  
    template_url=scan.struct_subjectSpace
    template_base=os.path.basename(scan.struct_subjectSpace)
    overlay_url=scan.zscore_subjectSpace
    overlay_base=os.path.basename(scan.zscore_subjectSpace)
    title="Original MRI scan + z-score image"
    Images = collections.namedtuple('Images', ['title','template_url', 'overlay_url','template_base','overlay_base'])
    print overlay_url
    print overlay_base
    img_obj=Images(title=title,template_url=template_url,template_base=template_base,overlay_url=overlay_url,overlay_base=overlay_base)

    return render_template('brain_db/scan_view.html', images=img_obj) # changed article to scan_view

@app.route('/mni_view')
@login_required
def mni_view():
    #url_bdir=settings.UPLOADED_IMAGES_URL
    #bdir=settings.UPLOADED_IMAGES_DEST 
    template_file = bdir + '/MNI152_T1_1.5mm.nii.gz'
    template_url  = url_bdir + '/MNI152_T1_1.5mm.nii.gz'
    # This is REST path on xnat database

    template_base=os.path.basename(template_url)
    overlay_url=None
    overlay_base=None
    title="Standard Space MRI"
    Images = collections.namedtuple('Images', ['title','template_url', 'overlay_url','template_base','overlay_base'])
    img_obj=Images(title=title,template_url=template_url,template_base=template_base,overlay_url=overlay_url,overlay_base=overlay_base)

    return render_template('brain_db/scan_view.html', images=img_obj) # changed article to scan_view

@app.route('/mni_zscore_view')
@login_required
def mni_zscore_view():
    user_id=session['user_id']
    scan=Scan.query.filter_by(user_id=user_id).first_or_404()
    #url_bdir=settings.UPLOADED_IMAGES_URL
    
    if not scan.zscore_mniSpace or not os.path.exists(url_bdir + scan.zscore_mniSpace): # retrieve the file from XNAT if not already exist locally
        #bdir=settings.UPLOADED_IMAGES_DEST 
         
        SUBJECT=str(user_id).zfill(4)
        EXPERIMENT=SUBJECT + "_MR1"
        SCAN='*' # Need to change so can find scan by scan type
        
        # here attempt to download zscore image. If doesn't exist then run the pipeline. Maybe better
        # to put this in a separate route that is activated by subject button press after validating the raw scan
        overlay_file = bdir + 'data/' + SUBJECT + '/' + EXPERIMENT + '/zscore_mniSpace.nii.gz'
        overlay_url  = url_bdir + 'data/' + SUBJECT + '/' + EXPERIMENT + '/zscore_mniSpace.nii.gz'
        overlay_path='/projects/' + PROJECT + '/subjects/' + SUBJECT + '/experiments/' + EXPERIMENT + '/scans/' + SCAN + '/resources/Zscores/files/Zscore_MNI.nii.gz'
        os.system('mkdir --parents ' + os.path.dirname(overlay_file))
        #scn_obj=xnat.select(overlay_path).get(overlay_file).first()
        import pyxnat
        xnat=pyxnat.Interface(config='/home/ubuntu/workspace/flask_brain_db/mind-xnat.cfg')
        scn_obj=xnat.select(overlay_path).first()
        
        # First check if file already exists locally 
        # if so then commit path to model
        if os.path.exists(overlay_file):
            scan.zscore_mniSpace=overlay_url
            db.session.commit()
            flash("MNI z-score image already downloaded from XNAT")
            #xnat.select(overlay_path).get(overlay_file)
        # If the zscore map exists on XNAT then download
        elif scn_obj.exists():
            xnat.select(overlay_path).first().get(overlay_file)
            scan.zscore_mniSpace=overlay_url
            db.session.commit()
            flash("MNI z-score image successfully downloaded from XNAT and local path committed to local DB")
        # If the file does not exist on xnat, then must run the pipeline
        elif not scn_obj.exists():
            # Here send curl action to start pipeline for VBM analysis. Will need to figure out how to do 
            # email notification to the user. Otherwise just say check back in an hour for now. 
            uri = """/data/projects/{}/pipelines/Segment_to_Zscore/experiments/{}?inbody=true""".format(PROJECT, scan.xnat_session_id)
            method='POST'
            xnat._exec(uri,method=method)
            flash("MNI Z-score map not generated yet. Please check back in 20 minutes!")
            return redirect(url_for('mni_view'))
        else:
            flash("Error obtaining or generating z-score file")
            return redirect(url_for('mni_view')) 
  
    template_url=url_bdir + '/MNI152_T1_1.5mm.nii.gz'
    template_base=os.path.basename(template_url)
    overlay_url=scan.zscore_mniSpace
    overlay_base=os.path.basename(scan.zscore_mniSpace)
    title="Standard MRI scan + z-score image"
    Images = collections.namedtuple('Images', ['title','template_url', 'overlay_url','template_base','overlay_base'])
    img_obj=Images(title=title,template_url=template_url,template_base=template_base,overlay_url=overlay_url,overlay_base=overlay_base)

    return render_template('brain_db/scan_view.html', images=img_obj) # changed article to scan_view

@app.route('/predict/<string:trait>')
@login_required
def predict(trait):
    user_id=session['user_id']
    scan=Scan.query.filter_by(user_id=user_id).first_or_404()
    user=User.query.filter_by(id=user_id).first_or_404()
    #url_bdir=settings.UPLOADED_IMAGES_URL
    #bdir=settings.UPLOADED_IMAGES_DEST 
    SUBJECT=str(user_id).zfill(4)
    EXPERIMENT=SUBJECT + "_MR1"
    SCAN='*' # Need to change so can find scan by scan type
         
    calculate=0 # for now recalculate each time
    
    predict_file = bdir + 'data/' + SUBJECT + '/' + EXPERIMENT + '/age_sex_predictions.json'
    predict_url  = url_bdir + 'data/' + SUBJECT + '/' + EXPERIMENT + '/age_sex_predictions.json'
    predict_path='/projects/' + PROJECT + '/subjects/' + SUBJECT + '/experiments/' + EXPERIMENT + '/scans/' + SCAN + '/resources/Predictions/files/age_sex_predictions.json'
    
    age_distro_file = bdir + 'data/' + SUBJECT + '/' + EXPERIMENT + '/age_distro.png'
    age_distro_url = url_bdir + 'data/' + SUBJECT + '/' + EXPERIMENT + '/age_distro.png'
    age_distro_path='/projects/' + PROJECT + '/subjects/' + SUBJECT + '/experiments/' + EXPERIMENT + '/scans/' + SCAN + '/resources/Predictions/files/age_distro.png'
    
    sex_distro_file = bdir + 'data/' + SUBJECT + '/' + EXPERIMENT + '/sex_distro.png'
    sex_distro_url = url_bdir + 'data/' + SUBJECT + '/' + EXPERIMENT + '/sex_distro.png'
    sex_distro_path='/projects/' + PROJECT + '/subjects/' + SUBJECT + '/experiments/' + EXPERIMENT + '/scans/' + SCAN + '/resources/Predictions/files/sex_distro.png'
    
    if not os.path.exists(os.path.dirname(predict_file)):
        os.system('mkdir --parents ' + os.path.dirname(predict_file))
    #scn_obj=xnat.select(overlay_path).get(overlay_file).first()
    import pyxnat
    xnat=pyxnat.Interface(config='mind-xnat.cfg')
    
    if calculate:
        # Here send curl action to start pipeline for VBM analysis. Will need to figure out how to do 
        # email notification to the user. Otherwise just say check back in an hour for now. 
        uri = """/data/projects/{}/pipelines/VBM8_predict_ageSex/experiments/{}?inbody=true""".format(PROJECT, scan.xnat_session_id)
        method='POST'
        xnat._exec(uri,method=method)
        flash("Updating age and sex predictions based on brain scan!")
        #time.sleep(10) # Give ten seconds for the file to be generated
        #return redirect(url_for('mni_view'))

    # first wait 5 seconds
    time.sleep(4)
    predict_obj=xnat.select(predict_path).first()
    while not predict_obj.exists():
        time.sleep(2)
        predict_obj=xnat.select(predict_path).first()
    else:
        xnat.select(predict_path).first().get(predict_file)
        xnat.select(age_distro_path).first().get(age_distro_file)
        xnat.select(sex_distro_path).first().get(sex_distro_file)
        
    # Reading data back
    with open(predict_file, 'r') as f:
        data = json.load(f)
    #return str(data["age"]) + "   " + str(data["prob_male"])
    
    if trait == 'age':
        age_diff = round(data["age"] - scan.scan_age,2)
        #data["age"]=round(data["age"],2)
        if age_diff > 0:
            txt_input="older"
        else:
            txt_input="younger"
        title="Your BrainAGE is " + str(age_diff) + " years " + txt_input + " than your real age"
        age_distro=age_distro_url
        sex_distro=[]
    elif trait == 'sex':
        data["prob_male"]=round(data["prob_male"],2)
        if user.sex == "Male":
            title = 'Your BrainSEX is ' + str(data["prob_male"]) + ' probability male'
        elif user.sex == "Female":
            value = 1 - data["prob_male"]
            title = 'Your BrainSEX is ' + str(value) + ' probability female'
        sex_distro=sex_distro_url
        age_distro=[]
    Images = collections.namedtuple('Images', ['title','age_distro', 'sex_distro'])
    img_obj=Images(title=title,age_distro=age_distro,sex_distro=sex_distro)
    return render_template('brain_db/scan_view.html', images=img_obj) # changed article to scan_view
    
@app.route('/set_vars_fun')    
@set_vars
def set_vars_fun():
    return SUBJECT
    
@app.route('/delete/<int:user_id>')
@owner_required
def delete(user_id):
    scan = Scan.query.filter_by(user_id=user_id).first_or_404()
    scan.live = False
    db.session.commit()
    flash("Scan deleted")
    return redirect('/admin')

#@app.route('/article/<slug>/comment', methods=('GET','POST'))
#@login_required
#def comment(slug):
#    form = CommentForm()
#    if form.validate_on_submit():
#        blog = Blog.query.first() # Assuming only one blog for this
#        author = Author.query.filter_by(username=session['username']).first()
#        post = Post.query.filter_by(slug=slug).first_or_404()
#        body = form.body.data
#        comment = Comment(blog, post, author, body)
#        db.session.add(comment)
#        db.session.commit()
#        
#        # Here get all comments for this post
#        all_comments=Comment.query.filter_by(post_id=post.id)
#        flash("comment created")
#        return redirect(url_for('article', slug=post.slug, comments=all_comments))
#    
    # get all comments to pass to the new render
    #comments = Comment.query.filter_by(post_id=post_id)    
#    return render_template('blog/comment.html', slug=slug, form=form)
