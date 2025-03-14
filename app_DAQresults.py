from flask import Flask, render_template, send_from_directory
import os
import glob
from flask import Blueprint
from flask import current_app
import logging as log

app_b = Blueprint('DAQresults', __name__)



# Base directory where images are stored
IMAGE_FOLDER = "/Users/noises/workspace/MultiModuleTeststandUI/DAQresults/"
NO_IMAGE = 'noimage.png'


DAQ_GENERATED_PLOTS = [
        "noise_vs_channel_chip0", "pedestal_vs_channel_chip0", "total_noise_chip0",
        "noise_vs_channel_chip1", "pedestal_vs_channel_chip1", "total_noise_chip1",
        "noise_vs_channel_chip2", "pedestal_vs_channel_chip2", "total_noise_chip2",
        "noise_vs_channel_chip3", "pedestal_vs_channel_chip3", "total_noise_chip3",
    ]

class DAQplots:
    def __init__(self, jobTAG, moduleID):
        self.module_id = moduleID
        if moduleID:
            self.plots =  { image: f'{jobTAG}/{self.module_id}/{image}.png' for image in DAQ_GENERATED_PLOTS }
    def GetFig(self,imageTYPE):
        if imageTYPE not in self.plots:
            log.warning(f'[DAQplots - InvalidImageType] "{ imageTYPE }" are not in the list "{ DAQ_GENERATED_PLOTS }"')
            return NO_IMAGE
        image_path = self.plots[imageTYPE]
        if not os.path.isfile(IMAGE_FOLDER + image_path):
            log.warning(f'[DAQplots - InvalidPath] "{ image_path }" should existed but nothing found.')
            return NO_IMAGE
        return self.plots[imageTYPE] if imageTYPE in self.plots else NO_IMAGE
class DAQplots_NOIMAGE(DAQplots):
    def __init__(self):
        self.module_id = ''
        pass
    def GetFig(self,imageTYPE):
        return NO_IMAGE

@app_b.route('/DAQresults')
def DAQresults():
    # Update this dictionary with actual image paths
    grid_pos = current_app.DAQimages.keys()
    related_module_id = [ current_app.DAQimages[pos].module_id for pos in grid_pos ]
    zipped_images = zip(grid_pos,related_module_id)

    return render_template("DAQresult.html", images=zipped_images, image_types=DAQ_GENERATED_PLOTS)

@app_b.route('/testDAQresults')
def testDAQresults(): # add a lot of fake data

    # Update this dictionary with actual image paths
    current_app.DAQimages = { module_id: DAQplots_NOIMAGE()
            for module_id in [
                'moduleID1L', 'moduleID1C', 'moduleID1R',
                'moduleID2L', 'moduleID2C', 'moduleID2R',
                'moduleID3L', 'moduleID3C', 'moduleID3R',
                'moduleID4L', 'moduleID4C', 'moduleID4R',
                'moduleID5L', 'moduleID5C', 'moduleID5R',
                'moduleID6L', 'moduleID6C', 'moduleID6R',
                'moduleID7L', 'moduleID7C', 'moduleID7R',
                'moduleID8L', 'moduleID8C', 'moduleID8R',
                ] }
    current_app.DAQimages['moduleID1L'] = DAQplots('run_bashjob1','32033148t5')
    current_app.DAQimages['moduleID1C'] = DAQplots('run_bashjob1','320XHB03PP00006')
    current_app.DAQimages['moduleID3C'] = DAQplots('run_bashjob1','32033148t5')
    current_app.DAQimages['moduleID5R'] = DAQplots('run_bashjob1','320XHB03PP00006')
    
    grid_pos = current_app.DAQimages.keys()
    related_module_id = [ current_app.DAQimages[pos].module_id for pos in grid_pos ]
    zipped_images = zip(grid_pos,related_module_id)


    return render_template("DAQresult.html", images=zipped_images, image_types=DAQ_GENERATED_PLOTS)

@app_b.route('/images/<gridPOSITION>/<imageTYPE>')
def get_image(gridPOSITION,imageTYPE=None):
    """ Serve images from the folder """

    return send_from_directory(IMAGE_FOLDER, current_app.DAQimages[gridPOSITION].GetFig(imageTYPE))



if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
