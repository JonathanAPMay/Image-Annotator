Additional resources need to be downloaded to fully make use of the program and without them, there is potential for crashes or lack of functionality.

For use of automatic segmentation:
https://drive.google.com/drive/folders/1TLiJHxHylT_lI2iP7FKyW05miAMsS8-u
This link holds two files which should be placed in the same directory as the python code, this is the pretrained model used within the project's code

As of right now, image formats accepted by the application are .png and .jpg with annotations being saved as .json files in COCO format.
"View Annotated Image" only works if there is a saved dataset file of the same name as the image being loaded, it should also be specified that the user should try to load an image as normal to use this option.
Adjusting line colour only affects the user's vision and this will not be saved as a property within the dataset file.
Saving of the segmentation mask is currently not working as the format provided by the ML model function does not synchronise with the mask save function.
Case is not considered when typing labels for annotations, any uppercase but identically spelt labels will be associated as the same label when saving.

Tester Source image found at:
https://www.pexels.com/photo/photo-of-living-room-1457842/