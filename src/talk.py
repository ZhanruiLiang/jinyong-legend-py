import config

lines = None

def init():
    global lines
    with open(config.talkfile) as talkfile:
        lines = [line.split('*') for line in talkfile]

def get_line(idx):
    return lines[idx]
