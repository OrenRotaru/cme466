# Pipeline Examples

These JSON pipelines are ready to open in CV Pipeline Lab (`Open`).

- `birds_contour_count_pipeline.json`: Count birds by contour boxes after thresholding + morphology.
- `cells_adaptive_contour_pipeline.json`: Adaptive thresholding is often more stable than a global threshold for uneven illumination.
- `cells_assignment_style_pipeline.json`: Direct mapping of the two-pass morphology + area-filter contour counting assignment workflow.
- `channel_split_merge_psnr_pipeline.json`: Shows channel split/merge and reconstruction quality check with PSNR.
- `coins_dual_contour_hough_pipeline.json`: Top branch: threshold+contours. Bottom branch: Hough circles. Merge for side-by-side comparison.
- `dlib_hog_face_optional_pipeline.json`: Requires `dlib` installed. This pipeline mirrors the course dlib HOG face detector examples.
- `family_haar_face_eye_pipeline.json`: Counts frontal faces while still drawing eyes and other detections.
- `hog_descriptor_study_pipeline.json`: Parameter study pipeline for HOG descriptor geometry and vector length.
- `license_plate_character_contours_pipeline.json`: Character counting template using adaptive threshold + contour filtering.
- `noisy_denoise_sharpen_compare_pipeline.json`: Branching template for denoise+sharpen vs original, with PSNR metric.
- `pedestrian_custom_cascade_pipeline.json`: Demonstrates custom cascade XML path usage.
- `ped1_hog_interactive_style_pipeline.json`: Mirrors the ped1 HOG detectMultiScale tuning workflow (stride/padding/scale) with score filtering + count output.
- `people_face_eye_lecture_style_pipeline.json`: Lecture-style face+eye workflow with face ellipses, eye circles, and separate face/eye counts.
- `people_hog_advanced_count_pipeline.json`: Replicates the HOG confidence-bucket style used in the FaceDetection notebook examples.
- `people_hog_vs_cascade_compare_pipeline.json`: Useful template for comparing two detectors on the same image via split/merge.
- `soccer_green_mask_contour_pipeline.json`: Template for HSV masking + morphology + contour counting.
- `video_frame_face_pipeline.json`: Still-image workflow but sourced from a chosen frame index of a video file.
