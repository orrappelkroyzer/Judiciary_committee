import pandas as pd
import sys
from pathlib import Path
local_python_path = str(Path(__file__).parents[0])
if local_python_path not in sys.path:
   sys.path.append(local_python_path)
from utils.utils import load_config, get_logger
logger = get_logger(__name__)
config = load_config(config_path=Path(local_python_path) / "config.json")
import plotly.express as px
from utils.plotly_utils import fix_and_write, get_colors
import numpy as np
import plotly.graph_objects as go
import re
import plotly
from datetime import timedelta
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
categories = ['יו״ר הוועדה', 'יו״ר וועדה חלופי', 'שר המשפטים', 'ח״כ הקואליציה', 'מומחה תומך', 'ח״כ האופוזיציה', 'מומחה מתנגד',
              'מנהל הועדה', 'יועמ"ש הכנסת', 'יועמ״ש הוועדה', 'עובד ציבור',  'דובר לא ידוע']

force=True


ZION_BEMISHPAT = "Zion Bemishpat" 
NATION_LAW = "Nation law"
law = ZION_BEMISHPAT

def analyze_speakers():
    logger.info("analyzing by speaker")
    tagging =pd.read_excel(Path(config['input_dir'])  / law / "speaker tagging.xlsx").set_index('שם דובר')['קטגוריה']
    fn = Path(config['input_dir']) / law / 'speaker_in_meeting_by_chairperson.xlsx'
    d = Path(config['input_dir']) / law / "processed_by_chairperson"
    
    def ananlyze_by_speaker_and_chairman(x):
        meeting_date = x.stem
        df = pd.read_excel(x)
        df['length'] = df.text.apply(lambda x: len(x.split()))
        df = df.join(df.groupby('chairman')['length'].sum().rename('total_length'), on='chairman')
        t1 = df.groupby(['name', 'chairman'])\
            .agg({'length' : 'sum', 'total_length' : 'first'})\
                .reset_index()\
                    .assign(meeting_date=meeting_date)
        t1['אחוז השתתפות בישיבה לפי חתך יו"ר'] = 100*t1['length']/t1['total_length']
        t1 = t1.drop(columns='total_length').rename(columns={'length' : "מס' מלים לפי חתך יור"})                         
        return t1
    df = pd.concat([ananlyze_by_speaker_and_chairman(x) for x in d.glob("*.xlsx")])\
        .rename(columns={'name' : 'שם דובר', 'chairman' : 'יו"ר', 'meeting_date' : 'תאריך הישיבה'})\
            .merge(tagging, on='שם דובר', how='left')
    df.reset_index(inplace=True)   
    logger.info(f"writing to {fn}")
    df.to_excel(fn, index=False)

    fn = Path(config['input_dir']) / law / 'speaker_in_meeting.xlsx'
    
    def ananlyze_by_speaker(x):
        meeting_date = x.stem
        df = pd.read_excel(x)
        df['length'] = df.text.apply(lambda x: len(x.split()))
        df['אורך קטע לא מופרע מקסימלי'] = df['length']
        df['ממוצע אורך קטע לא מופרע'] = df['length']
        t2 = df.groupby('name')\
            .agg({'length' : 'sum', 'אורך קטע לא מופרע מקסימלי' : 'max', 'ממוצע אורך קטע לא מופרע' : 'mean'})\
                .reset_index()\
                    .assign(meeting_date=meeting_date)
        t2['אחוז השתתפות בישיבה'] = 100*t2['length']/t2.length.sum()
        t2 = t2.rename(columns={'length' : "מס' מלים"})                         
        return t2
    df = pd.concat([ananlyze_by_speaker(x) for x in d.glob("*.xlsx")])\
        .rename(columns={'name' : 'שם דובר', 'chairman' : 'יו"ר', 'meeting_date' : 'תאריך הישיבה'})\
            .merge(tagging, on='שם דובר', how='left')
    df.reset_index(inplace=True) 
    df['שם דובר'] = df['שם דובר'].apply(lambda x: x.split(" (")[0])
    logger.info(f"writing to {fn}")
    df.to_excel(fn, index=False)
    
        
    return

def split_by_chairperson():
    logger.info("extracting chairperson")
    source_dir = Path(config['input_dir']) / law / "processed"
    target_dir = Path(config['input_dir']) / law / "processed_by_chairperson"
    target_dir.mkdir(parents=True, exist_ok=True)
    for x in source_dir.glob("*.xlsx"):
        name = x.stem
        if  (target_dir /f'{name}.xlsx').exists() and not force:
            continue
        df = pd.read_excel(x)
        t = df.loc[df['name'].str.startswith("היו\"ר"), 'name']
        df['chairman_segment'] = (t.shift(1, fill_value=t.head(1)) != t).cumsum()
        df['chairman_segment'] = df['chairman_segment'].ffill()
        df['chairman'] = df['chairman_segment'].replace(df.groupby('chairman_segment')['name'].first().to_dict())
        df.to_excel(target_dir /f'{name}.xlsx', index=False)



def process_formal_protocol():
    logger.info("porocessing formal protocol")
    
    
    folder = Path(config['input_dir']) / law / 'formal_protocol'
    target_folder = Path(config['input_dir']) / law / 'processed'
    target_folder.mkdir(parents=True, exist_ok=True)
    for filename in folder.glob('*.txt'):
        logger.info(f"working on {filename}")
        name = filename.stem
        if law == ZION_BEMISHPAT:
            speaker_pat = re.compile(r'<< \w+ >> (.+?): << \w+ >>', re.UNICODE|re.MULTILINE) # for files=7? check if regex works better
        elif law == NATION_LAW:
            if name == '20180712':
                speaker_pat = re.compile(r'<< \w+ >> (.+?): << \w+ >>', re.UNICODE|re.MULTILINE) # for files=7? check if regex works better
            else:
                speaker_pat = re.compile(r'\n(.*):\n', re.UNICODE|re.MULTILINE)
        else:
            assert False
        
        
        if  (target_folder /f'{name}.xlsx').exists() and not force:
            logger.info("File exists, ignoring")
            continue
        else:
            text_file = open(filename, "r", encoding= 'utf8')
            txt = text_file.read()
            text_file.close() 
            if law == NATION_LAW:
                reg = "הצעת חוק\-יסוד: ישראל \– מדינת הלאום של העם היהודי"
                txt = re.split(reg, txt)[-1]
            speaker_text = re.split(speaker_pat, txt)
            speakers = []
            texts = []
            for i in range(1, int(len(speaker_text)/2)+1):
                texts.append(speaker_text[i*2])
                speakers.append(speaker_text[i*2-1].strip())
            df = pd.DataFrame(data={'file':name,'name':speakers,'text':texts})
            df.text = df.text.apply(lambda x: x.replace("\n",''))
            df.text = df.text.apply(lambda x: x.replace("-",''))
            logger.info(f"writing to {target_folder} / {name}.xlsx'")
            df.to_excel(target_folder /f'{name}.xlsx', index=False, engine='xlsxwriter')

def process_whisper():
    speaker_pat = re.compile(r"([^\n]+)\n([^\n]+)\n\n+", re.UNICODE|re.MULTILINE)

def mp42wav():
    folder = Path(r"C:\Users\orkro\Desktop\audio")
    for mp3 in folder.glob("*.mp4"):
        wav = mp3.parent / f"{mp3.stem}.wav"
        logger.info(f"translating {mp3} to {wav}")
        if wav.exists() and not force:
            logger.info(f"{wav} exists, skipping")
            continue
        
        clip = VideoFileClip(str(mp3))
        clip.audio.write_audiofile(wav)

def mp32wav():
    folder = Path(r"C:\Users\orkro\Desktop\audio")
    for mp3 in folder.glob("*.mp3"):
        wav = mp3.parent / f"{mp3.stem}.wav"
        logger.info(f"translating {mp3} to {wav}")
        if wav.exists() and not force:
            logger.info(f"{wav} exists, skipping")
            continue
        
        sound = AudioSegment.from_mp3(mp3)
        sound.export(wav, format="wav")



def process_diarization():
    folder = Path(config['input_dir']) / law / 'rttm'
    dfs = []
    for fn in folder.glob("*.rttm"):
        logger.info(f"working on {fn.stem}")
        df = pd.read_csv(fn, sep=" ", header=None, \
            names=["Type", "File ID", "Channel ID", "Turn Onset", "Turn Duration", "Orthography Field", "Speaker Type", "Speaker Name", "Confidence Score", "Signal Lookahead Time"])
        df['זמן התחלה'] = df['Turn Onset'].apply(lambda x: f"{int(x/3600):02}:{int(x/60)%60:02}:{int(x%60):02}")
        
        df = df[['File ID', "Speaker Name", 'זמן התחלה', "Turn Duration"]].rename(columns={'File ID' : 'תאריך', "Speaker Name" : 'שם דובר',  "Turn Duration" : 'משך'})
        df.index.name = 'אינדקס'
        df.to_excel(Path(config['input_dir']) / law / 'processed_audio' / f"{fn.stem}.xlsx")
        df.groupby('שם דובר')['משך'].sum().sort_values(ascending=False).reset_index().to_excel(Path(config['input_dir']) / law / 'processed_audio' / f"{fn.stem}_distribution.xlsx")
        dfs += [df]
    pd.concat(dfs).reset_index().rename(columns={'index' : 'אינדקס בתוך הישיבה'}).to_excel(Path(config['input_dir']) / law / 'processed_audio' / "all_meetings.xlsx")
    
    
def main():
    process_formal_protocol()
    split_by_chairperson()
    analyze_speakers()
    # mp32wav()
    # mp42wav()
    # process_diarization()

if __name__ == "__main__":             
    main()