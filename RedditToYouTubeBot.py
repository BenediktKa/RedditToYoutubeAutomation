
import praw

from datetime import datetime

import unicodedata

import time

import math

from PIL import Image, ImageDraw, ImageFont
import textwrap

from gtts import gTTS

import string
from mutagen.mp3 import MP3
import shutil

import cv2
import os

from natsort import natsorted, ns

from pydub import AudioSegment
import ffmpeg
import moviepy.editor as mp
import glob

# Config
import json
with open('config.json') as config_file:
    config = json.load(config_file)

# Voice
import tts.sapi
voice = tts.sapi.Sapi()
voice.set_rate(config['voice']['speed'])
voice.set_voice('Vocalizer Expressive Daniel Harpo 22kHz')

def makeVideo(audioTimes, imageDir, qNum, title):

    # Multiplies everything by framerate
    audioTimes = [math.ceil(x * config['video']['framerate']) for x in audioTimes]

    video_name = 'res/video' + str(qNum)
    fileType = '.avi'

    imagesTemp = []
    images = []

    for img in os.listdir(imageDir):
        if (img.endswith('.png')):
            imagesTemp.append(img)

    # Sort images in natural order
    imagesTemp = natsorted(imagesTemp, key = lambda y: y.lower())

    i = 0
    for img in imagesTemp:
        if (img.startswith(str(qNum))):
            images.append(img)

        i += 1

    print(images)

    frame = cv2.imread(os.path.join(imageDir, images[0]))
    height, width, layers = frame.shape

    video = cv2.VideoWriter(video_name + fileType, 0, config['video']['framerate'], (config['video']['width'], config['video']['height']))

    i = 0
    for image in images:
        print(audioTimes[i])
        for j in range (0, int(audioTimes[i])):
            video.write(cv2.imread(os.path.join(imageDir, image)))
        i += 1

    cv2.destroyAllWindows()
    video.release()
    mergeAudio(video_name, qNum, title)

def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def mergeAudio(videoFile, qNum, title):

    voicesDir = 'res/voice'
    voices = [img for img in os.listdir(voicesDir) if (img.endswith('.mp3') and img.startswith(str(qNum)))]

    #sort voices in natural order
    voices = natsorted(voices, key=lambda y: y.lower())

    audioFile = AudioSegment.empty()
    i = 0
    for voice in voices:
        singleFile = AudioSegment.from_mp3('res/voice/' + voice)
        audioFile += singleFile
        i += 1

    # writing mp3 files is a one liner
    audioFile.export('res/voice' + str(qNum) + '.mp3', format='mp3')

    video = mp.VideoFileClip('res/video' + str(qNum) + '.avi')

    video.write_videofile('res/final/final '+ str(qNum) +'.mp4', audio='res/voice' + str(qNum) + '.mp3')

    clearDirectories()

    # uploadToYouTube(qNum, title)

def uploadToYouTube(qNum, title):
    fileName = 'res/final/final ' + str(qNum)
    title = title.replace("\"", "")
    title = title.replace("\'", "")
    print(title)
    cmd = "python upload_video.py --file='" + fileName + ".mp4' --title='Top Ask Reddit of Yesterday' --description='Ask Reddit: " + title + "' --keywords='meme'"
    print(cmd)
    os.system(cmd)

def clearDirectories():
    files = glob.glob('res/images/*')
    for f in files:
        os.remove(f)
    files = glob.glob('res/voice/*')
    for f in files:
        os.remove(f)

def createImages(text, score, author, time, imagePrefix):

    audioTimes = []

    text = text.replace("*","")

    screenSize = (config['video']['width'], config['video']['height'])
    fontSize = 40


    font = ImageFont.truetype("Verdana.ttf", fontSize)
    authorFont = ImageFont.truetype("Verdana.ttf", int(fontSize / 1.5))
    timeFont = ImageFont.truetype("Verdana.ttf", int(fontSize / 1.5))
    scoreFont = ImageFont.truetype("Verdana.ttf", int(fontSize / 1.5))

    textArray = textwrap.wrap(text, width = 3000 / fontSize)

    numberOfLines = screenSize[1] / (fontSize * 1.5) - 2


    numberOfFiles = int(len(textArray) / numberOfLines) + 1


    j = 0
    currentLine = 0

    for j in range (0, numberOfFiles):
        textOnPage = ''
        backgroundImage = Image.open(config['style']['commentsBackground'])
        backgroundImageDraw = ImageDraw.Draw(backgroundImage)

        textWidth, textHeight = backgroundImageDraw.textsize(text, font)


        for k in range (0, int(numberOfLines)):
            if (currentLine == len(textArray)):
                break

            s = textArray[currentLine]
            textOnPage += ' '
            textOnPage += s
            authorPos = (325, 178)
            timePos = (700, 178)
            scorePos = (75, 490)

            textPos = (275, fontSize * 1.5 * ((currentLine % numberOfLines) + 5))
            backgroundImageDraw.text(textPos, s, fill = 'white', font = font, anchor='None')

            backgroundImageDraw.text(authorPos, author, fill = 'white', font = authorFont, anchor = 'None')

            backgroundImageDraw.text(timePos, time, fill = 'white', font = authorFont, anchor = 'None')

            backgroundImageDraw.text(scorePos, str(score), fill = 'white', align = 'center', font = scoreFont, anchor = 'None')

            currentLine += 1

        backgroundImage.save('res/images/' + imagePrefix + '-' + str(j) + ".png")

        audioTimes.append(createVoice(textOnPage, 'res/voice/' + imagePrefix + '-' + str(j) + ".wav"))

    staticName = 'res/images/' + fileName + '-static.png'

    shutil.copy('res/static.png', staticName)

    staticName = 'res/voice/' + fileName + '-static.mp3'
    shutil.copy('res/static.mp3', staticName)
    staticAudio = MP3('res/static.mp3')
    audioTimes.append(truncate(staticAudio.info.length, 1))
    return audioTimes



def createTitleImage (text, imagePrefix):

    audioTimes = []

    screenSize = (config['video']['width'], config['video']['height'])
    #print(novo)
    fontSize=60


    font = ImageFont.truetype("Verdana.ttf", fontSize)
    authorFont = ImageFont.truetype("Verdana.ttf", int(fontSize/1.5))


    textArray = textwrap.wrap(text, width=2200/fontSize)



    blank_image = Image.new('RGBA', screenSize, 'white')
    img_draw = ImageDraw.Draw(blank_image)

    currentLine=0
    for s in textArray:
        textPos = (20, fontSize*1.5* ( (currentLine) + 1 ))
        img_draw.text(textPos, s, fill='black', font=font, anchor='None')
        currentLine+=1

    blank_image.save('res/images/' + imagePrefix + '-0-0-a' + ".png")
    audioTimes.append(createVoice(text, 'res/voice/' + imagePrefix + '-0-0-a' + ".wav"))

    staticName = 'res/images/' + imagePrefix + '-0-0-static.png'

    shutil.copy('res/static.png', staticName)

    staticName = 'res/voice/' + imagePrefix + '-0-0-static.mp3'
    shutil.copy('res/static.mp3', staticName)
    staticAudio = MP3('res/static.mp3')
    audioTimes.append(truncate(staticAudio.info.length, 1))
    return audioTimes




def createVoice (text, fileName):

    audioTime = 0
    try:
        voice.create_recording(fileName, text)
        os.chdir(config['general']['workingDir'])
        AudioSegment.from_wav(fileName).export(fileName.replace('.wav', '.mp3'), format="mp3")

        audio = MP3(fileName.replace('.wav', '.mp3'))
        audioTime = truncate(audio.info.length, 1)


    except Exception as e:
        print('Failed to create voice: ', e)

    return audioTime


# ------------ Main Code ------------



# create the objects from the imported modules

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

topPosts = subreddit.top(config['reddit']['topFilter'])
gildedPosts = subreddit.gilded()

postIDs = []
postTitles = []
postComments = []
postCommentsScore = []
postCommentsTime = []
authorNames = []




for submission in topPosts:
    if submission.score > config['general']['scoreFilter']:
        postIDs.append(submission.id)

i = 0
for id in postIDs:
    postComments.append([])
    postCommentsScore.append([])
    postCommentsTime.append([])
    authorNames.append([])

    post = reddit.submission(id=id)
    print(post.title)

    postTitles.append(post.title)

    post.comment_sort = 'top'
    allComments = post.comments
    charCount = 0
    for comment in allComments:
        if comment.stickied:
            continue

        if charCount > config['reddit']['maxCharacterComment']:
            break

        formattedComment = comment.body
        formattedDate = datetime.utcfromtimestamp(comment.created_utc).strftime('%H:%M:%S | %d.%m.%Y')
        score = comment.score
        try:
            authorName = comment.author.name
        except Exception as e:
            authorName = "<deleted>"

        postComments[i].append(formattedComment)
        postCommentsScore[i].append(score)
        postCommentsTime[i].append(formattedDate)
        authorNames[i].append(authorName)

        charCount += len(formattedComment)

    i += 1


print('------------ Top Threads Found ------------')

for i in range (0, len(postComments)):
    questionArray = postComments[i]
    questionScoreArray = postCommentsScore[i]
    questionTimeArray = postCommentsTime[i]
    authorArray = authorNames[i]
    audioTimes = []
    audioTimes += createTitleImage(postTitles[i], str(i))
    for j in range(0, len(questionArray)):
        comment = questionArray[j]
        score = questionScoreArray[j]
        time = questionTimeArray[j]
        author = authorArray[j]
        fileName = str(i) + '-' + str(j)
        audioTimes += createImages(comment, score, author, time, fileName)


    makeVideo(audioTimes, 'res/images', i, postTitles[i])