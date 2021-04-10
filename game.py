import cv2
import imutils
import math
from random import random

# global variables

# debug var
debug = True
# Average background var
avg_bg = None
# Difficulty mode
game_mode = None
# Determines if a match is on or it is timeout
play = True
# Main font for displayed text
font = cv2.FONT_HERSHEY_SIMPLEX

# Choice vars
rock_count = 0
paper_count = 0
scissors_count = 0

# Score vars
wins = 0
draws = 0
loses = 0

# final result
result = ""
# Time out var between matches
counter = 150

# Find the average background
def find_avg_bg(image, weight):
    global avg_bg
    # initialize the background
    if avg_bg is None:
        avg_bg = image.copy().astype("float")
        return

    # compute weighted average, accumulate it and update the background
    cv2.accumulateWeighted(image, avg_bg, weight)


# Find the hand
def find_hand(image, threshold=25):
    global avg_bg
    # find the absolute difference between background and current frame
    diff = cv2.absdiff(avg_bg.astype("uint8"), image)

    # threshold the diff image so that we get the foreground
    thresholded = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)[1]

    # get the contours in the thresholded image
    cnts = cv2.findContours(thresholded.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

    # return None, if no contours detected
    if len(cnts) == 0:
        return
    else:
        # based on contour area, get the maximum contour which is the hand
        segmented = max(cnts, key=cv2.contourArea)
        return (thresholded, segmented)


# Count the fingers
def count_fingers(segmented, frame):
    global rock_count,scissors_count,paper_count

    # smoothen the contour a little
    epsilon = 0.0005 * cv2.arcLength(segmented, True)
    approx = cv2.approxPolyDP(segmented, epsilon, True)

    # make convex hull around hand
    hull = cv2.convexHull(segmented)

    # define area of hull and area of hand
    areahull = cv2.contourArea(hull)
    areacnt = cv2.contourArea(segmented)

    # check the we are not deviding by 0
    if areacnt != 0:
        # find the percentage of area not covered by hand in convex hull
        arearatio = ((areahull - areacnt) / areacnt) * 100

    # make convex hull around the smoothend contour of the hand
    hull = cv2.convexHull(approx, returnPoints=False)

    # prevent "The convex hull indices are not monotonous" error
    try:
        # find the defects in convex hull with respect to hand
        defects = cv2.convexityDefects(approx, hull)
    except:
        if debug:
            print("ERROR")
        return
    # var that will hold the number of fingers
    l=0

    # check if there are defects
    if defects is None:
        return

    # if defects were found loop them
    for i in range(defects.shape[0]):
        s, e, f, d = defects[i, 0]
        start = tuple(approx[s][0])
        end = tuple(approx[e][0])
        far = tuple(approx[f][0])

        # find length of all sides of triangle
        a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
        b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
        c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)
        s = (a + b + c) / 2
        ar = math.sqrt(s * (s - a) * (s - b) * (s - c))

        # distance between point and convex hull
        d = (2 * ar) / a

        # apply cosine rule here
        angle = math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)) * 57

        # ignore angles > 90 and ignore points very close to convex hull(they generally come due to noise)
        if angle <= 90 and d > 30:
            # add finger
            l += 1

    # add finger
    l += 1

    # print corresponding gestures which are in their ranges
    # if it has one finger
    if l == 1 and arearatio < 12:
        # display "Rock" text
        cv2.putText(frame, 'Rock', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)
        # add to the rock counter
        rock_count= rock_count + 1
    # if it has two finger
    elif l == 2:
        # display "Scissors" text
        cv2.putText(frame, 'Scissors', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)
        # add to the scissors counter
        scissors_count = scissors_count + 1
    # if it has five finger
    elif l == 5:
        # display "Paper" text
        cv2.putText(frame, 'Paper', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)
        # add to the paper counter
        paper_count = paper_count + 1
    # everything other then 1,2 or 5 fingers is an error
    else:
        # display "Error" text
        cv2.putText(frame, 'Error', (10, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)

    # when the the first counter to reach 40 that move will be played by the user, before returning the move the counters will be reset
    if paper_count > 40:
        paper_count = 0
        rock_count = 0
        scissors_count = 0
        return "PAPER"
    elif scissors_count > 40:
        paper_count = 0
        rock_count = 0
        scissors_count = 0
        return "SCISSORS"
    elif rock_count > 40:
        paper_count = 0
        rock_count = 0
        scissors_count = 0
        return "ROCK"

# Logic for easy mode
def easyMode(choice):
    num = random()
    # if the user selected easy mode he has 40% to win or draw and 20% to lose
    if choice == "ROCK":
        if num < 0.4:
            return "ROCK"
        elif num > 0.4 and num < 0.8:
            return "SCISSORS"
        else:
            return "PAPER"
    elif choice == "SCISSORS":
        if num < 0.4:
            return "SCISSORS"
        elif num > 0.4 and num < 0.8:
            return "PAPER"
        else:
            return "ROCK"
    else:
        if num < 0.4:
            return "PAPER"
        elif num > 0.4 and num < 0.8:
            return "ROCK"
        else:
            return "SCISSORS"
# Logic for medium mode
def mediumMode(choice):
    num = random()
    # if the user selected medium mode he has 33% to win, draw or lose
    if choice == "ROCK":
        if num < 0.3:
            return "ROCK"
        elif num > 0.3 and num < 0.6:
            return "SCISSORS"
        else:
            return "PAPER"
    elif choice == "SCISSORS":
        if num < 0.3:
            return "SCISSORS"
        elif num > 0.3 and num < 0.6:
            return "PAPER"
        else:
            return "ROCK"
    else:
        if num < 0.3:
            return "PAPER"
        elif num > 0.3 and num < 0.6:
            return "ROCK"
        else:
            return "SCISSORS"
# Logic for hard mode
def hardMode(choice):
    num = random()
    # if the user selected hard mode he will ether draw or lose (50% draw, 50% lose)
    if choice == "ROCK":
        if num < 0.5:
            return "ROCK"
        else:
            return "PAPER"
    elif choice == "SCISSORS":
        if num < 0.5:
            return "SCISSORS"
        else:
            return "ROCK"
    else:
        if num < 0.5:
            return "PAPER"
        else:
            return "SCISSORS"

# Find the result of the match
def analyse(pc_choice, choice):
    global wins, draws, loses, result

    # check if it is a draw
    if choice == pc_choice:
        # update score
        draws = draws + 1
        # get the final result
        result = "DRAW"
    # check if it is lost
    elif choice == "ROCK" and pc_choice == "PAPER":
        # update score
        loses = loses + 1
        # get the final result
        result = "LOST"
    # check if it is won
    elif choice == "ROCK" and pc_choice == "SCISSORS":
        # update score
        wins = wins + 1
        # get the final result
        result = "WON"
    # check if it is won
    elif choice == "PAPER" and pc_choice == "ROCK":
        # update score
        wins = wins + 1
        # get the final result
        result = "WON"
    # check if it is lost
    elif choice == "PAPER" and pc_choice == "SCISSORS":
        # update score
        loses = loses + 1
        # get the final result
        result = "LOST"
    # check if it is won
    elif choice == "SCISSORS" and pc_choice == "PAPER":
        # update score
        wins = wins + 1
        # get the final result
        result = "WON"
    # check if it is lost
    elif choice == "SCISSORS" and pc_choice == "ROCK":
        # update score
        loses = loses + 1
        # get the final result
        result = "LOST"

    if debug:
        print("USER: {} - PC: {}".format(choice,pc_choice))
        print("RESULT: {}".format(result))


if __name__ == "__main__":

    # Display the instructions and wait for user confirmation
    while(True):

        # the instructions
        print("Firstly you will be asked to choose a difficulty mode.\n"
              "After choosing a mode a window will pop up it will show your camera feed and a green square.\n"
              "For the first 2-3 seconds don't make any movement inside the green square.\n"
              "After 3 seconds put your hand in the green square in a form of a rock, paper(fingers wide apart) or scissors.\n"
              "Keep your hand there until you see the result of the match in center of the window.\n"
              "After a couple of seconds the result message will be cleared and you can play another match.\n"
              "You can not play the game while the result message is displayed.\n"
              "Try to play the game in a room with good lighting and make sure that green square is filming a single colored background without any objects.\n"
              "To exit the game press 'q' on your keyboard.\n"
              "Do you understand?(yes)\n")
        # the user input
        tmp = input()

        # Check if input is correct
        if( tmp == "yes"):
            break

    # Display the difficulty modes and wait for the user to choose one
    while(True):

        # the difficulty modes
        print("\nChoose a level of difficulty:\n"
              "1. Easy\n"
              "2. Medium\n"
              "3. Hard\n")

        # get the user input
        game_mode = int(input())

        # check if the user input is correct
        if game_mode <= 3 and game_mode > 0:
            break

    # initialize accumulated weight
    weight = 0.5

    # get the reference to the webcam
    camera = cv2.VideoCapture(1)

    # region of interest (ROI) coordinates
    top, right, bottom, left = 10, 350, 225, 590

    # initialize num of frames
    num_frames = 0

    # keep looping, until interrupted
    while (True):
        # get the current frame
        (grabbed, frame) = camera.read()

        # resize the frame
        frame = imutils.resize(frame, width=700)

        # flip the frame so that it is not the mirror view
        #frame = cv2.flip(frame, 1)

        # clone the frame
        clone = frame.copy()

        # get the ROI
        roi = frame[top:bottom, right:left]

        # convert the roi to grayscale and blur it
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)

        # to get the background, keep looking till a threshold is reached
        # so that our weighted average model gets calibrated
        if num_frames < 30:
            find_avg_bg(gray, weight)
            if num_frames == 1 and debug:
                print("Please wait while the program is calibrating...")
            elif num_frames == 29 and debug:
                print("Calibration successfull!")
        else:
            # segment the hand region
            hand = find_hand(gray)

            # check whether the hand has been found
            if hand is not None:

                # if a hand has been found, unpack the thresholded image and segmented region
                (thresholded, segmented) = hand

                # display the contours of the hand in the main window
                cv2.drawContours(clone, [segmented + (right, top)], -1, (0, 0, 255), 2 )

                # check if the match is on or is in timeout
                if play:
                    # count the number of fingers and get the shape (rock, paper or scissors)
                    choice = count_fingers(segmented, clone)

                # var that holds the computers move
                pc_choice = ""

                # check if the match is on and if the user has made a move
                if choice != None and play:
                    # implement easy mode logic
                    if game_mode == 1:
                        pc_choice = easyMode(choice)
                    # implement medium mode logic
                    elif game_mode == 2:
                        pc_choice = mediumMode(choice)
                    # implement hard mode logic
                    else:
                        pc_choice = hardMode(choice)
                    # find the result of the match
                    analyse(pc_choice,choice)

                    # set the game on timeout
                    play = False
                    # reset the hand var
                    hand = None

                if debug:
                    # show the thresholded image
                    cv2.imshow("Thesholded", thresholded)

        # draw the segmented hand
        cv2.rectangle(clone, (left, top), (right, bottom), (0, 255, 0), 2)

        # increment the number of frames
        num_frames += 1

        # check if the match is no on
        if not play:
            # check if the user won
            if result == "WON":
                # display victory message
                cv2.putText(clone, "YOU WON", (250, 300), font, 1, (0, 255, 0), 2,
                        cv2.LINE_AA)
            # check if the user lost
            elif result == "LOST":
                # display defeat message
                cv2.putText(clone, "YOU LOST", (250, 300), font, 1, (0, 0, 255), 2,
                            cv2.LINE_AA)
            # check if the user drew
            elif result == "DRAW":
                # display tie message
                cv2.putText(clone, "DRAW", (250, 300), font, 1, (255, 0, 0), 2,
                            cv2.LINE_AA)
            # count down till the next match
            counter = counter - 1
            # check if the timeout has passed
            if counter == 0:
                # start the next match
                play = True
                # reset timeout counter
                counter = 150
        # show score
        cv2.putText(clone, "W: {} D: {} L: {}".format(wins, draws, loses), (0, 500), font, 1, (0, 0, 255), 2,
                    cv2.LINE_AA)

        # display the frame with segmented hand
        cv2.imshow("Video Feed", clone)

        # if the user pressed "q", then stop looping
        if cv2.waitKey(10) == ord("q"):
            print("Goodbye!")
            break

# free up memory
camera.release()
cv2.destroyAllWindows()