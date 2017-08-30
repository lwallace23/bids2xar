import os
import fnmatch
import ntpath
import sys
from os.path import basename
from lxml import etree

# input dir should be root directory of bids dataset
inputdir = sys.argv[-1]

# get root directory name for project name by default
splitdir = os.path.split(os.path.dirname(inputdir))

# handle windows path if os.path fails (eg cygwin)
if splitdir[0] == '':
    project = ntpath.split(inputdir)[1]
else:
    project = splitdir[1]

# register XNAT namespace for XML generation
xnatns = "http://nrg.wustl.edu/xnat"
etree.register_namespace("xnat", xnatns)

xnatprefix = "{" + xnatns + "}"

# move into root directory
os.chdir(inputdir)

print os.getcwd()

# inventory subject directories
subjectdirs = [d for d in os.listdir(".") if os.path.isdir(d)]

# iterate through subject directories
for subjectdir in subjectdirs:
    os.chdir(subjectdir)

    # use subject directory for subject label by default
    subjectl = subjectdir.split('-')[1]

    # use subject and 'MR' for session label by default
    sessionl = subjectl + "_MR"

    #print os.getcwd()

    # build MR session XML, set session-level metadata
    session = etree.Element(xnatprefix + 'mrSessionData')
    
    session.set('label', sessionl)
    session.set('project', project)
    subject = etree.SubElement(session, xnatprefix + 'subject_ID')
    subject.text = subjectl
    scans = etree.SubElement(session, xnatprefix + 'scans')

    # iterate through subdirectories, get directory piece
    datadirs = [d for d in os.listdir(".") if os.path.isdir(d)]

    # if directory has nifti (.nii or .nii.gz)
    for datadir in datadirs:
        # XNAT scan ID is BIDS image type folder (anat, func, etc) plus index,
        # eg anat1, anat2, func1, func2, func3.. reset index at each subfolder
        imageindex = 0

        # descend into data image type folder
        os.chdir(datadir)

        # find all NIFTI files
        niftifiles = fnmatch.filter(os.listdir("."), "*.nii.gz")

        # generate scan metadata from filename for each NIFTI file
        for niftifile in niftifiles:
            # count files, XNAT scan ID is image type folder plus file index
            imageindex += 1
            id = datadir + str(imageindex)

            # tokenize BIDS filename
            metadata = niftifile.split('.')[0].split('_')

            # modality comes last, will be XNAT scan type
            type = metadata[-1]

            # XNAT series description will be everything after subject
            seriesdesc = "_".join(metadata[1:])

            # generate scan XML metadata
            #print id + "   " + type + "   " + seriesdesc
            scan = etree.SubElement(scans, xnatprefix + 'scan')
            scan.set('ID', id)
            scan.set('type', type)

            seriesdescel = etree.SubElement(scan, xnatprefix + 'series_description')
            seriesdescel.text = seriesdesc

        os.chdir("..")

    # print out XML for debugging
    print etree.tostring(session, pretty_print=True)

    # back up to go to next subject
    os.chdir("..")
