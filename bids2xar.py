import os
import fnmatch
import ntpath
import sys
from os.path import basename
from lxml import etree

# register XNAT namespace for XML generation
xnatns = "http://nrg.wustl.edu/xnat"
xsins = "http://nrg.wustl.edu/xsi"

etree.register_namespace("xnat", xnatns)
etree.register_namespace("xsi", xsins)

xnatprefix = "{" + xnatns + "}"
xsiprefix = "{" + xsins + "}"

# output directory should be last argument
outputdir = sys.argv[-1]

outputdir = os.path.abspath(outputdir)

if not outputdir.endswith('/') or not outputdir.endswith('\\'):
    outputdir = outputdir + '/'

# input dir should be root directory of bids dataset
inputdir = sys.argv[-2]

# get root directory name for project name by default
splitdir = os.path.split(os.path.dirname(inputdir))

# handle windows path if os.path fails (eg cygwin)
if splitdir[0] == '':
    project = ntpath.split(inputdir)[1]
else:
    project = splitdir[1]

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

    # build MR session XML, set session-level metadata
    session = etree.Element(xnatprefix + 'MRSession')
    tree = etree.ElementTree(session)

    session.set('ID', '')
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
            imageindex += 1

            # count files, XNAT scan ID is image type folder plus file index
            id = datadir + str(imageindex)

            # tokenize BIDS filename
            metadata = niftifile.split('.')[0].split('_')

            # modality comes last, will be XNAT scan type
            type = metadata[-1]

            # XNAT series description will be everything after subject
            seriesdesc = "_".join(metadata[1:])

            # generate scan XML metadata
            # print id + "   " + type + "   " + seriesdesc
            scan = etree.Element(xnatprefix + 'scan')
            scan.set('ID', id)
            scan.set('type', type)
            scan.set(xsiprefix + 'type', 'xnat:mrScanData')

            seriesdescel = etree.SubElement(scan, xnatprefix + 'series_description')
            seriesdescel.text = seriesdesc

            fileel = etree.SubElement(scan, xnatprefix + 'file')
            fileel.set('content', 'NIFTI_RAW')
            fileel.set('format', 'NIFTI_RAW')
            fileel.set('URI', niftifile)
            fileel.set(xsiprefix + 'type', 'xnat:imageResource')

            scans.append(scan)

        os.chdir("..")

    # print out XML for debugging
    print etree.tostring(session, pretty_print=True)

    # write XML to temp file
    try:
        filename = outputdir + 'assessment' + subjectl + '.xml'
        print filename
        tree.write(open(filename, 'wb'))
    except IOError as e:
        print 'IO Error'

    # back up to go to next subject
    os.chdir("..")
