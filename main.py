import numpy as np
import cv2 as cv
import Person
import time

try:
    log = open('log.txt', "w")
except:
    print("No log")

count_up = 0
count_down = 0

# Constants
TOTAL_SEATS_IN_LIB = 100

cap = cv.VideoCapture('Test_Files/TestVideo.avi')


for i in range(19):
    print(i, cap.get(i))

h = 480
w = 640
frameArea = h*w
areaTH = frameArea/250
print('Area Threshold', areaTH)

line_up = int(2*(h/5))
line_down = int(3*(h/5))

up_limit = int(1*(h/5))
down_limit = int(4*(h/5))

print("Red line y:", str(line_down))
print("Blue line y:", str(line_up))
line_down_color = (255, 0, 0)
line_up_color = (0, 0, 255)
pt1 = [0, line_down]
pt2 = [w, line_down]
pts_L1 = np.array([pt1, pt2], np.int32)
pts_L1 = pts_L1.reshape((-1, 1, 2))
pt3 = [0, line_up]
pt4 = [w, line_up]
pts_L2 = np.array([pt3, pt4], np.int32)
pts_L2 = pts_L2.reshape((-1, 1, 2))

pt5 = [0, up_limit]
pt6 = [w, up_limit]
pts_L3 = np.array([pt5, pt6], np.int32)
pts_L3 = pts_L3.reshape((-1, 1, 2))
pt7 = [0, down_limit]
pt8 = [w, down_limit]
pts_L4 = np.array([pt7, pt8], np.int32)
pts_L4 = pts_L4.reshape((-1, 1, 2))

fgbg = cv.createBackgroundSubtractorMOG2(detectShadows=True)

kernelOp = np.ones((3, 3), np.uint8)
kernelOp2 = np.ones((5, 5), np.uint8)
kernelCl = np.ones((11, 11), np.uint8)

# Variables
font = cv.FONT_HERSHEY_SIMPLEX
persons = []
max_p_age = 5
pid = 1

while (cap.isOpened()):
    ret, frame = cap.read()

    for i in persons:
        i.age_one()

    fgmask = fgbg.apply(frame)
    fgmask2 = fgbg.apply(frame)

    try:
        ret, imBin = cv.threshold(fgmask, 200, 255, cv.THRESH_BINARY)
        ret, imBin2 = cv.threshold(fgmask2, 200, 255, cv.THRESH_BINARY)
        # Opening
        mask = cv.morphologyEx(imBin, cv.MORPH_OPEN, kernelOp)
        mask2 = cv.morphologyEx(imBin2, cv.MORPH_OPEN, kernelOp)
        # Closing
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernelCl)
        mask2 = cv.morphologyEx(mask2, cv.MORPH_CLOSE, kernelCl)
    except:
        print('EOF')
        print('UP:', count_up)
        print('DOWN:', count_down)
        break

    contours0, hierarchy = cv.findContours(
        mask2, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    for count in contours0:
        area = cv.contourArea(count)
        if area > areaTH:

            M = cv.moments(count)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            x, y, w, h = cv.boundingRect(count)

            new = True
            if cy in range(up_limit, down_limit):
                for i in persons:
                    if abs(x-i.getX()) <= w and abs(y-i.getY()) <= h:
                        new = False
                        i.updateCoords(cx, cy)
                        if i.going_UP(line_down, line_up) == True:
                            count_up += 1
                            print("ID:", i.getId(), 'crossed going up at',
                                  time.strftime("%c"))
                            log.write(
                                "ID: "+str(i.getId())+' crossed going up at ' + time.strftime("%c") + '\n')
                        elif i.going_DOWN(line_down, line_up) == True:
                            count_down += 1
                            print("ID:", i.getId(),
                                  'crossed going down at', time.strftime("%c"))
                            log.write(
                                "ID: " + str(i.getId()) + ' crossed going down at ' + time.strftime("%c") + '\n')
                        break
                    if i.getState() == '1':
                        if i.getDir() == 'down' and i.getY() > down_limit:
                            i.setDone()
                        elif i.getDir() == 'up' and i.getY() < up_limit:
                            i.setDone()
                    if i.timedOut():
                        index = persons.index(i)
                        persons.pop(index)
                        del i
                if new == True:
                    p = Person.MyPerson(pid, cx, cy, max_p_age)
                    persons.append(p)
                    pid += 1
            cv.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            img = cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    for i in persons:
        cv.putText(frame, str(i.getId()), (i.getX(), i.getY()),
                   font, 0.3, i.getRGB(), 1, cv.LINE_AA)

    str_up = f'Leaving: {count_up}'
    str_down = f'Comming: {count_down}'

    frame = cv.polylines(frame, [pts_L1], False, line_down_color, thickness=2)
    frame = cv.polylines(frame, [pts_L2], False, line_up_color, thickness=2)
    frame = cv.polylines(frame, [pts_L3], False, (255, 255, 255), thickness=1)
    frame = cv.polylines(frame, [pts_L4], False, (255, 255, 255), thickness=1)

    # Up/Leaving text
    cv.putText(frame, str_up, (10, 40), font, 0.5,
               (255, 255, 255), 2, cv.LINE_AA)
    cv.putText(frame, str_up, (10, 40), font, 0.5, (0, 0, 255), 1, cv.LINE_AA)

    # Down/Comming text
    cv.putText(frame, str_down, (10, 90), font,
               0.5, (255, 255, 255), 2, cv.LINE_AA)
    cv.putText(frame, str_down, (10, 90), font,
               0.5, (255, 0, 0), 1, cv.LINE_AA)

    # Number of people in Library
    people = count_down - count_up
    no_of_people_in_lib = f'People in Library: {people}'
    cv.putText(frame, no_of_people_in_lib, (10, 140), font,
               0.5, (255, 255, 255), 2, cv.LINE_AA)
    cv.putText(frame, no_of_people_in_lib, (10, 140), font,
               0.5, (255, 0, 0), 1, cv.LINE_AA)

    # Number of seats remaining in Library
    seats = f'Number of Seats in Library: {TOTAL_SEATS_IN_LIB - people}'
    cv.putText(frame, seats, (10, 190), font,
               0.5, (255, 255, 255), 2, cv.LINE_AA)
    cv.putText(frame, seats, (10, 190), font,
               0.5, (255, 0, 0), 1, cv.LINE_AA)

    cv.imshow('Frame', frame)
    # cv.imshow('Mask', mask)

    k = cv.waitKey(30) & 0xff
    if k == 27:
        break


log.flush()
log.close()
cap.release()
cv.destroyAllWindows()
