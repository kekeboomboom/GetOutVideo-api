from pytubefix import YouTube
link = "https://www.youtube.com/watch?v=TZN_eL_wubQ"
video = YouTube(link)
print(video.title) # Works