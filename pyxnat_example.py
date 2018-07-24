import pyxnat, os
# connect to xnat instance. Enter server and then username and password or config file)
xnat=pyxnat.Interface(server=server_URL)

# Define project name, subject and experiment label. For this exercise make sure these exist first and that the 
# experiment folder has a SCAN child with a NIFTI resources subfolder with a T1 structural scan.nii.gz
PROJECT='TEST'
SUBJECT='0001'
EXPERIMENT='0001_MR1'

proj_obj=xnat.select.project(PROJECT)

# Below will print all the custom variable names (at Subject and Experiment level)
print proj_obj.get_custom_variables() 

# Create subject and experiment objects, and verify they exist
sub_obj=proj_obj.subject(SUBJECT) 
exp_obj=sub_obj.experiment(EXPERIMENT)
print sub_obj.exists()
print exp_obj.exists()

# Below for getting and sending files
SCAN='T1' 

# Below is the full path where the downloaded file will be stored and saved to
downloaded_file = '/path/to/downloads/' + 'scan.nii.gz'
# Below is the xnat path to the file you want to download
xnat_file_path='/projects/' + PROJECT + '/subjects/' + SUBJECT + '/experiments/' + EXPERIMENT + '/scans/' + SCAN + '/resources/NIFTI/files/scan.nii.gz'
# The below command downloads the file to the specified path. Note you can also rename the file by changing scan.nii.gz to i.e. renamed.nii.gz
# 
xnat.select(xnat_file_path).get(downloaded_file)
# or 
xnat.select(xnat_file_path).first().get(downloaded_file)
# If SCAN was set to '*'

# # Below is to uploaded a file to a new resources directory, here called OUTPUT for the same subject

scan_type='T1 weighted structural'
upload_file = '/path/to/uploads/' + 'output.nii.gz'

exp_obj.scan(SCAN).resource('OUTPUT').file(os.path.basename(upload_file)).insert(
                upload_file,
                content=scan_type,
                overwrite=True,
                type=scan_type, 
                format='NIFTI')


# Below is syntax for setting and retrieving custom variable 'sub_var1' at the Subject level
# Note custom variables are case insensitive, so should always use lower case letters and with underscores
sub_obj.attrs.set("xnat:subjectData/fields/field[name='sub_var1']/field",'150')
val = sub_obj.xpath("/xnat:Subject/xnat:fields/xnat:field[@name='sub_var1']/text()[2]")

# Below command should print out '150'
print val

# Below is syntax for setting and retrieving custom variable 'exp_var1' at the Experiment level
exp_obj.attrs.set("xnat:mrSessionData/fields/field[name='exp_var1']/field",'100')
val = exp_obj.xpath("/xnat:MRSession/xnat:fields/xnat:field[@name='exp_var1']/text()[2]")

# Below should print out '100'
print val
