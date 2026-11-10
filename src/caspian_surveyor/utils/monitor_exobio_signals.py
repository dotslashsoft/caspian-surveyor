import cv2
import mss
import numpy as np
import time


def detect_green_highlights(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_green = np.array([35, 80, 80])
    upper_green = np.array([90, 255, 255])

    mask = cv2.inRange(hsv, lower_green, upper_green)
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    bounding_boxes = []

    for contour in contours:
        if cv2.contourArea(contour) < 50:
            continue

        x, y, width, height = cv2.boundingRect(contour)
        bounding_boxes.append(
            (x, y, width, height)
        )

    return bounding_boxes

def draw_target_brackets(frame, box):
    x, y, width, height = box

    color = (230, 230, 0)  # BGR: subdued cyan
    thickness = 1
    corner = min(12, width // 3, height // 3)

    cv2.line(frame, (x, y), (x + corner, y), color, thickness)
    cv2.line(frame, (x, y), (x, y + corner), color, thickness)

    cv2.line(frame, (x + width, y),
             (x + width - corner, y), color, thickness)
    cv2.line(frame, (x + width, y),
             (x + width, y + corner), color, thickness)

    cv2.line(frame, (x, y + height),
             (x + corner, y + height), color, thickness)
    cv2.line(frame, (x, y + height),
             (x, y + height - corner), color, thickness)

    cv2.line(frame, (x + width, y + height),
             (x + width - corner, y + height), color, thickness)
    cv2.line(frame, (x + width, y + height),
             (x + width, y + height - corner), color, thickness)

def define_region_of_interest():
    with mss.MSS() as screen:
        primary_monitor = screen.monitors[1]

        region_width = primary_monitor["width"] // 3
        region_height = primary_monitor["height"] // 3

        upper_left_x = primary_monitor["left"] + region_width
        upper_left_y = primary_monitor["top"] + region_height

        return {
            "left": upper_left_x,
            "top": upper_left_y,
            "width": region_width,
            "height": region_height
        }

def monitor_screen(stop_event, update_callback):
    region = define_region_of_interest()
    with mss.MSS() as screen:
        target_fps = 15
        frame_interval = 1.0 / target_fps

        while not stop_event.is_set():
            frame_start = time.perf_counter()

            screenshot = screen.grab(region)

            frame = np.asarray(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            bounding_boxes = detect_green_highlights(frame)

            update_callback(bounding_boxes)

            elapsed = time.perf_counter() - frame_start
            remaining = max(0.0, frame_interval - elapsed)

            stop_event.wait(remaining)


if __name__ == "__main__":
    pass