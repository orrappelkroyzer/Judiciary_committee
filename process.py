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
from datetime import date


ZION_BEMISHPAT = "Zion Bemishpat" 
NATION_LAW = "Nation law"
law = NATION_LAW

categories = ['יו״ר הוועדה', 'יו״ר וועדה חלופי', 'שר המשפטים', 'ח״כ הקואליציה', 'מומחה תומך', 'ח״כ האופוזיציה', 'מומחה מתנגד',
              'מנהל הועדה', 'יועמ"ש הכנסת', 'יועמ״ש הוועדה', 'עובד ציבור',  'דובר לא ידוע']
if law == NATION_LAW:
    categories = ['יו״ר הוועדה', 'יו״ר וועדה חלופי', 'שר המשפטים', 'ח״כ הקואליציה', 'מומחה', 'ח״כ האופוזיציה', 'מומחה מתנגד',
              'מנהל הועדה', 'יועמ"ש הוועדה', 'יועמ״ש הוועדה', 'עובד ציבור',  'דובר לא ידוע']
colors = ['rgb(253,50,22)', # red
             'rgb(0,254,53)', #green
             'rgb(106,118,252)', # blue 
             'rgb(254,212,196)', # peach 
             'rgb(254,0,206)', # pink 
             'rgb(13,249,255)', # light blue
             'rgb(246,249,38)', # yellow
             'rgb(255,150,22)', # orange
             'rgb(71,155,85)', # dark green
             'rgb(238,166,251)', # light purple
             'rgb(220,88,125)', # dark pink
             'rgb(214,38,255)'] #


def p(l,t):
    return [l[i-1] for i in t]



def by_category_comparison(df):    
    logger.info("runnign conmapison by category")
    
    if law == ZION_BEMISHPAT:
        df.loc[~df['תאריך הישיבה'].isin(['22.1.23', '23.1.23', '30.1.23']), 'ימי דיונים'] = '11-18.1'
        df.loc[df['תאריך הישיבה'].isin(['22.1.23', '23.1.23', '30.1.23']), 'ימי דיונים'] = '22-23.1'
        df1 = df.assign(**{'ימי דיונים' : 'כל הישיבות'})
        df = [df, df1]
        t_colors=colors
    else:
        df['ימי דיונים'] = 'כל הישיבות'
        df = df[df["קטגוריה"].notnull()]
        t_colors = [
            'rgb(253,50,22)', # red
            'rgb(0,254,53)', #green
            'rgb(254,212,196)', # blue 
            'rgb(254,0,206)', # peach 
            'rgb(13,249,255)', # pink 
            'rgb(0,0,0)', # light blue
            'rgb(106,118,252)',# yellow
            'rgb(71,155,85)', # orange
            'rgb(255,150,22)', # dark green
            'rgb(220,88,125)', # light purple
            'rgb(0,0,0)', # dark pink
            'rgb(214,38,255)'#purple
        ]
    df = df.join(pd.Series(len(categories), index=categories, name='category order'), on='קטגוריה')
    df = df.sort_values('קטגוריה', ascending=True)
    fig = px.pie(df.reset_index(), 
                 values="מס' מלים",  
                 names="קטגוריה", 
                 title="אחוז ההשתפות לפי קטגוריה", 
                #  facet_col='ימי דיונים', 
                #  facet_col_spacing=0.15,
                 color_discrete_sequence=colors,
                 category_orders={'קטגוריה' : categories})
    fig.update_traces(textfont_size=25)
    fig.update_layout(legend={#'traceorder' : 'reversed',
                              'font' : {'size' : 25}},
                             # 'orientation' : "h",
                            #   'entrywidth' : 0.2, # change it to 0.3
                            #   'entrywidthmode' : 'fraction',
                            #   'xanchor' : 'center', 'yanchor' : 'bottom', 'x' : 0.5, 'y' : 0},
                      title_font={'size' : 25})

    fix_and_write(fig=fig,
                    filename="by_categories_comparison",
                    output_dir=config['output_dir'] / law)
                    #height_factor=0.75,
                    # width_factor=0.9)

def chairpersons_comparison():
    logger.info("runnign chairperson graph")
    d = Path(config['input_dir']) / law / "processed_by_chairperson"
    def foo(x):
        meeting_date = x.stem
        df = pd.read_excel(x)
        df['length'] = df.text.apply(lambda x: len(x.split()))
        if df.empty:
            return pd.DataFrame()
        return pd.DataFrame(df.groupby('chairman').apply(lambda g: 100*g.loc[g['name'] == g['chairman'], 'length'].sum()/g.length.sum())\
                .rename('אחוז מסך המלים בפרוטוקול'))\
                    .reset_index()\
                        .assign(meeting_date=meeting_date)
    by_chairman = pd.concat([foo(x) for x in d.glob("*.xlsx") if date.fromisoformat(f"{x.stem[:4]}-{x.stem[4:6]}-{x.stem[6:8]}") <= date(2018,3,30)])
    by_chairman['meeting_date'] = by_chairman['meeting_date'].str.replace('afternoon', 'אחה"צ')
    by_chairman = by_chairman.rename(columns={'meeting_date' : 'תאריך הישיבה'})
    by_chairman['יו"ר, תאריך הישיבה'] = by_chairman['chairman'] + ", " + by_chairman['תאריך הישיבה']
    by_chairman = by_chairman.rename(columns={'chairman' : 'יו"ר'})
    if law == ZION_BEMISHPAT:
        by_chairman['day'] = by_chairman['תאריך הישיבה'].apply(lambda x: int(x.split(".")[0]))
    else:
        by_chairman['day'] = by_chairman['תאריך הישיבה']
    t = by_chairman.sort_values('אחוז מסך המלים בפרוטוקול', ascending=True)
    fig = px.bar(t, y='יו"ר, תאריך הישיבה', x='אחוז מסך המלים בפרוטוקול', 
                 title=f'שיעור השתתפות של היו"ר (בחלק הישיבה בה כיהן כיו"ר) בפרוטוקול ועדת חוקה', 
                 orientation='h',  
                 category_orders={'index': t.index[::-1]}, 
                 color='יו"ר')
    fig.update_layout( yaxis={'categoryorder':'array', 'categoryarray':t['יו"ר, תאריך הישיבה']},
                        title={'xanchor': 'center', 'x':0.5},
                        legend={'traceorder' : 'reversed', 'xanchor' : 'right', 'yanchor' : 'top', 'y' : 0.8})
    fix_and_write(fig=fig,
                    filename="by_chairman_older_protocols_decending_order",
                    output_dir=config['output_dir'] / law,
                    height_factor=0.8,
                    width_factor=0.8)


 
def speaker_comparison(df):
    for meeting_date in df['תאריך הישיבה'].unique():
        t_colors = colors#[len(colors)-df[df['תאריך הישיבה'] == meeting_date]['קטגוריה'].nunique():]
        fig = px.bar(df[df['תאריך הישיבה'] == meeting_date].sort_values('אחוז השתתפות בישיבה', ascending=False), 
                     y='שם דובר', 
                     x='אחוז השתתפות בישיבה', 
                     title=f'שיעור השתתפות של דוברים שונים בפרוטוקול ועדת חוקה {meeting_date}', 
                     orientation='h', 
                     color='קטגוריה',
                     color_discrete_sequence=t_colors[::-1],
                     category_orders={'קטגוריה' : categories[::-1]})
        fig.update_layout(legend={'traceorder' : 'reversed', 
                                  'xanchor' : 'right', 'yanchor' : 'top', 'y' : 0.93})
        (config['output_dir'] / law /  "by_meeting" / "num_minutes").mkdir(parents=True, exist_ok=True)
        
        fix_and_write(fig=fig,
                    filename=meeting_date,
                    height_factor=1.5,
                    output_dir=config['output_dir'] / law / "by_meeting" / "num_minutes")

        fig = px.bar(df[df['תאריך הישיבה'] == meeting_date].sort_values('אורך קטע לא מופרע מקסימלי', ascending=False), 
                     y='שם דובר', 
                     x='אורך קטע לא מופרע מקסימלי', 
                     title=f' אורך מקסימלי של קטע דיבור לא מופרע למשתתף{meeting_date}', 
                     orientation='h', 
                     color='קטגוריה',
                     color_discrete_sequence=t_colors[::-1],
                     category_orders={'קטגוריה' : categories[::-1]})
        fig.update_layout(legend={'traceorder' : 'reversed', 
                                  'xanchor' : 'right', 'yanchor' : 'top', 'y' : 0.93})
        (config['output_dir'] / law /  "by_meeting" / "max_segment").mkdir(parents=True, exist_ok=True)
        fix_and_write(fig=fig,
                    filename=meeting_date,
                    height_factor=1.5,
                    output_dir=config['output_dir'] / law / "by_meeting" / "max_segment")
        fig = px.bar(df[df['תאריך הישיבה'] == meeting_date].sort_values('ממוצע אורך קטע לא מופרע', ascending=False), 
                     y='שם דובר', 
                     x='אורך קטע לא מופרע מקסימלי', 
                     title=f' אורך ממוצע של קטע דיבור לא מופרע למשתתף{meeting_date}', 
                     orientation='h', 
                     color='קטגוריה',
                     color_discrete_sequence=t_colors[::-1],
                     category_orders={'קטגוריה' : categories[::-1]})
        fig.update_layout(legend={'traceorder' : 'reversed', 
                                  'xanchor' : 'right', 'yanchor' : 'top', 'y' : 0.93})
        (config['output_dir'] / law / "by_meeting" / "mean_segment").mkdir(parents=True, exist_ok=True)
        fix_and_write(fig=fig,
                    filename=f"meeting_date",
                    height_factor=1.5,
                    output_dir=config['output_dir'] / law / "by_meeting" / "mean_segment")



    return df

def chairman_averages(speaker_in_meeting_by_chairperson):
    pd.DataFrame(speaker_in_meeting_by_chairperson.groupby('יו"ר').apply( \
        lambda g: 100*g.loc[g['שם דובר'] == g['יו"ר'], "מס' מלים לפי חתך יור"].sum() / \
                g["מס' מלים לפי חתך יור"].sum())\
                    .rename('אחוז מסך המלים בפרוטוקול'))\
                        .to_excel(config['output_dir'] / law / "chairperson_ave.xlsx")


def create_histogram_with_outliers(series, name, end, range=None):
    start = int(series.min())
    if range is None:
        size = 5
        # Making a histogram
        largest_value = series.max()
        if largest_value > end:
            hist = np.histogram(series, bins=list(range(start, end+size, size)) + [largest_value], weights=series)
        else:
            hist = np.histogram(series, bins=list(range(start, end+size, size)) + [end+size], weights=series)
    else:
        hist = np.histogram(series, bins=range, weights=series)

    # Adding labels to the chart
    labels = []
    for i, j in zip(hist[1][0::1], hist[1][1::1]):
        if j <= end:
            labels.append('{} - {}'.format(i, j))
        else:
            labels.append('> {}'.format(i))

    # Plotting the graph
    return go.Bar(x=labels,  y=hist[0], name=name)

def word_seg_histograms():
    d = Path(config['input_dir']) / "older meetings"
    df = pd.concat([pd.read_excel(x) for x in d.glob("*_processed.xlsx")]).reset_index()
    df = df.drop(columns=[x for x in df.columns if x.startswith("Unnamed")])
    df["מס' מלים"] = df.text.apply(lambda x: len(x.split()))

    tagging =pd.read_excel(Path(config['input_dir'])  / "speaker tagging.xlsx").set_index('שם דובר')['קטגוריה']
    df = df.rename(columns={'name' : 'שם דובר', 'chairman' : 'יו"ר', 'meeting_date' : 'תאריך הישיבה'})\
            .merge(tagging, on='שם דובר', how='left')

    data = [
        create_histogram_with_outliers(df.loc[df['שם דובר'] == 'היו"ר שמחה רוטמן', "מס' מלים"], "שמחה רוטמן", 
                                        end=250, range=[0,3,6,10,20,30, 40, 50, 100, 250]),
        create_histogram_with_outliers(df.loc[df['קטגוריה'] == 'ח״כ האופוזיציה', "מס' מלים"], 'ח"כים מהאופוזיציה',
                                        end=250, range=[0,3,6,10,20,30, 40, 50, 100, 250]),
    ]
    layout = go.Layout(
        title="היסטוגרמת אורכי קטע הדיבור ללא הפרעה"
    )
    fig = go.Figure(data=data, layout=layout)
    fix_and_write(fig=fig,
                    filename="segs_histogram",
                    #height_factor=1.5,
                    output_dir=config['output_dir'])

    return fig

def read_db():
    speaker_in_meeting_by_chairperson = pd.read_excel(Path(config['input_dir']) / law / 'speaker_in_meeting_by_chairperson.xlsx')
    speaker_in_meeting = pd.read_excel(Path(config['input_dir']) / law / 'speaker_in_meeting.xlsx')
    return speaker_in_meeting_by_chairperson, speaker_in_meeting

def main():
    
    speaker_in_meeting_by_chairperson, speaker_in_meeting = read_db()
    speaker_in_meeting = speaker_in_meeting[
        speaker_in_meeting['תאריך הישיבה'].apply(lambda x: date.fromisoformat(f"{x[:4]}-{x[4:6]}-{x[6:8]}")) <= date(2018,3,30)]
    logger.info(speaker_in_meeting)
    speaker_comparison(speaker_in_meeting)
    by_category_comparison(speaker_in_meeting)
    chairpersons_comparison()
    

if __name__ == "__main__":             
    main()