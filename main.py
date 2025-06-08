from flask import Flask, jsonify, request
from pydicom.dataset import Dataset
from pynetdicom import AE, debug_logger
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind
from datetime import datetime

app = Flask(__name__)

@app.route("/dicoms/<ip>/<port>/<ae_title>")
def dicoms(ip, port, ae_title):
    debug_logger()

    port = int(port)

    ae = AE(ae_title='DEFAULT_VALUE')
    ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)

    assoc = ae.associate(ip, port, ae_title=ae_title)
    if not assoc.is_established:
        print("Failed to associate")
        return []

    # Create query dataset filtering StudyDate = today
    today_str = datetime.now().strftime('%Y%m%d')
    ds = Dataset()
    ds.QueryRetrieveLevel = 'STUDY'
    ds.StudyDate = today_str  # Filter studies from today
    ds.PatientName = ''        # Return PatientName
    ds.StudyInstanceUID = ''   # Return StudyInstanceUID
    ds.StudyDescription = ''   # Return StudyDescription (optional)
    ds.StudyTime = ''          # Return StudyTime (optional)
    ds.PatientSex = ''
    ds.PatientID = request.args.get('patient_id', '')
    ds.ModalitiesInStudy = request.args.get('modality', '')
    ds.InstitutionName = request.args.get('institution_name', '') 

    results = []

    for (status, identifier) in assoc.send_c_find(ds, StudyRootQueryRetrieveInformationModelFind):
        if status and status.Status in (0xFF00, 0xFF01):
            # status 0xFF00 or 0xFF01 means pending results
            # Defensive: use .get() and str() to avoid errors
            study = {
                'PatientName': str(identifier.get('PatientName', '')),
                'StudyInstanceUID': str(identifier.get('StudyInstanceUID', '')),
                'StudyDescription': str(identifier.get('StudyDescription', '')),
                'StudyDate': str(identifier.get('StudyDate', '')),
                'StudyTime': str(identifier.get('StudyTime', '')),
                'PatientSex': str(identifier.get('PatientSex', '')),
                'PatientID': str(identifier.get('PatientID', '')),
                'ModalitiesInStudy': str(identifier.get('ModalitiesInStudy', '')),
                'InstitutionName': str(identifier.get('InstitutionName', '')),
            }
            results.append(study)
        else:
            # Finished or error
            break

    assoc.release()
    return jsonify(results), 200

if __name__=="__main__":
    app.run(debug=True)
