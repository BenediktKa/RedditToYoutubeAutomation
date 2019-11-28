import praw
from praw.models import MoreComments

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from PIL import Image
from io import BytesIO
import time
import os
import soundfile as sf
import ffmpeg
import moviepy.editor as mp
from natsort import natsorted, ns
import math
import cv2
import glob

from pydub import AudioSegment

# Config
import json
with open('config.json') as config_file:
    config = json.load(config_file)

# Voice
import tts.sapi
voice = tts.sapi.Sapi()
voice.set_rate(config['voice']['speed'])
voice.set_voice('Vocalizer Expressive Daniel Harpo 22kHz')

def scrollToBottom():
    SCROLL_PAUSE_TIME = 0.5

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Find more replies buttons
        #try:
        #    divs = driver.find_elements_by_xpath("//*[contains(text(), 'more replies')]")
        #    print('Numbers of divs found:', len(divs))

        #    for div in divs:
        #        div.click()
        #except:
        #    print('No Reply more buttons')

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)


        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def createVoice(text, fileName):

    audioTime = 0
    try:
        voice.create_recording(fileName, text)
        os.chdir(config['general']['workingDir'])

        sound = sf.SoundFile(fileName)
        audioTime = len(sound) / sound.samplerate

        fillerTime = 1 - (audioTime - int(audioTime))


        emptyFiller = AudioSegment.silent(duration = math.ceil(fillerTime * 1000))
        unfilledSound = AudioSegment.from_wav(fileName)

        finalSound = unfilledSound + emptyFiller

        finalSound.export(fileName, format = 'wav')

        sound = sf.SoundFile(fileName)
        audioTime = truncate(len(sound) / sound.samplerate, 1)
        print('Final Audio Time', audioTime)





    except Exception as e:
        print('Failed to create voice: ', e)

    return audioTime

def formatImages(imageDir):
    images = []

    for image in os.listdir(imageDir):
        if (image.endswith('.png')):
            images.append(image)

    for image in os.listdir(imageDir):
        foregroundImage = Image.open(os.path.join(imageDir, image), 'r')
        foregroundWidth, foregroundHeight = foregroundImage.size
        backgroundImage = Image.open(config['style']['commentsBackground'])
        backgroundWidth, backgroundHeight = backgroundImage.size
        offset = ((backgroundWidth - foregroundWidth) // 2, (backgroundHeight - foregroundHeight) // 2)
        backgroundImage.paste(foregroundImage, offset)
        backgroundImage.save('images/a' + image)

    for image in images:
        os.remove(os.path.join(imageDir, image))


def makeVideo(audioTimes, imageDir, videoNumber):

    # Multiplies everything by framerate
    audioTimes = [x * config['video']['framerate'] for x in audioTimes]

    videoName = 'video' + str(videoNumber)
    fileType = '.avi'

    images = []

    for img in os.listdir(imageDir):
        if (img.endswith('.png')):
            images.append(img)

    # Sort images in natural order
    images = natsorted(images, key = lambda y: y.lower())

    print('Images to make video from:', images)
    video = cv2.VideoWriter(videoName + fileType, 0, config['video']['framerate'], (config['video']['width'], config['video']['height']))

    i = 0
    for image in images:
        print('Processing Image', i)
        print('Frames to write:', audioTimes[i])

        frame = cv2.imread(os.path.join(imageDir, images[i]))

        for j in range (0, int(audioTimes[i])):
            video.write(frame)

        i += 1

    cv2.destroyAllWindows()
    video.release()
    mergeAudio(videoName, videoNumber)

def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def mergeAudio(videoFile, videoNumber):

    voicesDir = 'voices'
    voices = [img for img in os.listdir(voicesDir) if (img.endswith('.wav'))]

    # Sort voices in natural order
    voices = natsorted(voices, key = lambda y: y.lower())

    audioFile = AudioSegment.empty()
    i = 0
    for voice in voices:
        singleFile = AudioSegment.from_wav('voices/' + voice)
        audioFile += singleFile
        i += 1

    # Writing mp3 files is a one liner
    audioFile.export('voices' + str(videoNumber) + '.mp3', format = 'mp3', bitrate='352k')

    video = mp.VideoFileClip('video' + str(videoNumber) + '.avi')

    video.write_videofile('final/final '+ str(videoNumber) +'.mp4', audio = 'voices' + str(videoNumber) + '.mp3')

    clearDirectories()

def clearDirectories():
    files = glob.glob('images/*')
    for file in files:
        os.remove(file)
    files = glob.glob('voices/*')
    for file in files:
        os.remove(file)

clearDirectories()


# Reddit Login
reddit = praw.Reddit(client_id = config['reddit']['clientID'],
                     client_secret = config['reddit']['clientSecret'],
                     username = config['reddit']['username'],
                     password = config['reddit']['password'],
                     user_agent = config['reddit']['userAgent'])

subreddit = reddit.subreddit(config['reddit']['subreddit'])
stream = subreddit.stream

# phrase to activate the bot
keyphrase = config['reddit']['activateCommand']

topPosts = subreddit.top(config['reddit']['timeFilter'])
gildedPosts = subreddit.gilded()

postIDs = []

profile = webdriver.FirefoxProfile()
profile.set_preference('permissions.default.desktop-notification', 1)
driver = webdriver.Firefox(executable_path = "geckodriver.exe", firefox_profile = profile)

for submission in topPosts:
    if submission.over_18:
        continue;
    if submission.score > config['general']['scoreFilter']:
        postIDs.append(submission.id)

i = 0
for id in postIDs:

    audioTimes = []

    #id = 'e07nci'
    post = reddit.submission(id = id)
    #post.comments.replace_more(limit = 2000)
    print('Found popular thread:', post.title)
    print('URL:', post.url)

    confirmation = input('Do you want to make a video out of this thread? (Y/N)')

    if confirmation.lower() == 'n':
        continue

    driver.get(post.url + '?sort=' + config['reddit']['filterBy'])

    try:
        driver.find_element_by_xpath("//button[contains(text(),'I Agree')]").click()
        driver.find_element_by_xpath("//button[contains(text(),'View entire discussion')]").click()
    except:
        print('Already accepted cookies')

    scrollToBottom()

    time.sleep(1)
    print('Taking Screenshots')
    post.comments.replace_more(limit = 0)
    post.comment_sort = config['reddit']['filterBy']
    charCount = 0

    j = 0
    element = driver.find_element_by_id('t3_' + id)
    screenshot = element.screenshot_as_png
    image = Image.open(BytesIO(screenshot))
    image.save('images/' + str(j) + '.png')
    audioTimes.append(createVoice(post.title, 'voices/' + str(j) + '.wav'))
    j += 1

    audioTimeTotal = 0

    for comment in post.comments:
        if isinstance(comment, MoreComments):
            break

        if comment.stickied:
            continue

        if config['reddit']['maxCharacterComment'] < len(comment.body):
            continue
        if config['reddit']['minCommentScore'] > comment.score:
            continue
        if comment.banned_by is not None:
            continue
        if comment.author == None:
            continue

        print('Comment found with score of:', comment.score)

        try:
            element = driver.find_element_by_id('t1_' + comment.id)
        except:
            print('Cannot find element')
            continue

        if element.size['height'] > config['video']['height']:
            continue

        screenshot = element.screenshot_as_png
        image = Image.open(BytesIO(screenshot))
        image.save('images/' + str(j) + '.png')
        audioTime = createVoice(comment.body, 'voices/' + str(j) + '.wav')
        audioTimes.append(audioTime)
        audioTimeTotal += audioTime
        time.sleep(1)
        j += 1

        if audioTimeTotal > config['reddit']['maxVideoMinutes'] * 60:
            print('Max minutes reached')
            break

        if config['reddit']['minCommentLimit'] <= j:
            print('Comment limit reached')
            break

    # Format Images
    print('Formatting Images')
    formatImages('images')

    # Make the video
    print('Creating Video')
    makeVideo(audioTimes, 'images', i)
    i += 1


print('------------ Finalized Video Creation ------------')