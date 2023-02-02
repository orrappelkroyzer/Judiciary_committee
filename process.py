import pandas as pd
import sys
from pathlib import Path
local_python_path = str(Path(__file__).parents[1])
if local_python_path not in sys.path:
   sys.path.append(local_python_path)
from utils.utils import load_config, get_logger
logger = get_logger(__name__)
config = load_config(add_date=False)
import plotly.express as px
from utils.plotly_utils import fix_and_write

def by_category_comparison():    
    logger.info("runnign conmapison by category")
    df1 = pd.read_excel(Path(config['input_dir']) / "protocols by order updated timestamp.xlsx")
    df1['תאריך הישיבה'] = '22.1.23'
    df = pd.read_excel(Path(config['input_dir']) / "protocols older meetings.xlsx")
    df = pd.concat([df, df1])
    df.index = range(len(df))

    tagging = pd.read_excel(Path(config['input_dir'])  / "speaker tagging.xlsx")
    tagging1 = pd.read_excel(Path(config['input_dir'])  / "speaker tagging.xlsx", sheet_name='22.1').rename(columns={'דובר' : 'שם דובר'})
    tagging = pd.concat([tagging.reset_index(drop=True), tagging1.reset_index(drop=True)])
    tagging = tagging.groupby('שם דובר')['קטגוריה'].first()
    tagging['אריאל קלנר'] = 'ח״כ הקואליציה'
    tagging['טלי גוטליב'] = 'ח״כ הקואליציה'
    tagging['יונתן מישרקי'] = 'ח״כ הקואליציה'
    tagging['משה סעדה'] = 'ח״כ הקואליציה'
    tagging['עמית הלוי'] = 'ח״כ הקואליציה'
    tagging['?'] = 'דובר לא ידוע'
    df = df.merge(tagging, on='שם דובר', how='left')
    t = df.groupby(['קטגוריה', 'ישיבות'])["מס' מלים"].sum().reset_index()
    t = t.rename(columns={'ישיבות' : 'ימי דיונים'})
    t['ימי דיונים'] = t['ימי דיונים'].replace({'11-16.1' : '11-18.1'})
    t.loc[9, "מס' מלים"] += 46
    t.drop(6)
    t = t.drop(6)
    fig = px.pie(t, values="מס' מלים",  names="קטגוריה", title="אחוז ההשתפות לפי קטגוריה, 11-23.1.2023", facet_col='ימי דיונים', facet_col_spacing=0.2)
    fig.update_layout(title={'xanchor': 'center', 'x':0.5})
    fix_and_write(fig=fig,
                    filename="by_chairman_older_protocols_decending_order.png",
                    output_dir=config['output_dir'],
                    height_factor=1/2,
                    width_factor=1/2)

def chairpersons():
    logger.info("runnign chairperson graph")
    d = Path(config['input_dir']) / "older meetings"
    def foo(x):
        meeting_date = x.stem[:-10]
        df = df = pd.read_excel(x)
        df['length'] = df.text.apply(lambda x: len(x.split()))
        return pd.DataFrame(df.groupby('chairman').apply(lambda g: 100*g.loc[g['name'] == g['chairman'], 'length'].sum()/g.length.sum())\
                .rename('אחוז מסך המלים בפרוטוקול'))\
                    .reset_index()\
                        .assign(meeting_date=meeting_date)
    by_chairman = pd.concat([foo(x) for x in d.glob("*_processed.xlsx")])
    by_chairman['meeting_date'] = by_chairman['meeting_date'].str.replace('afternoon', 'אחה"צ')
    by_chairman = by_chairman.rename(columns={'meeting_date' : 'תאריך הישיבה'})
    by_chairman['יו"ר, תאריך הישיבה'] = by_chairman['chairman'] + ", " + by_chairman['תאריך הישיבה']
    by_chairman = by_chairman.rename(columns={'chairman' : 'יו"ר'})
    t = by_chairman.sort_values('אחוז מסך המלים בפרוטוקול', ascending=True)
    fig = px.bar(t, y='יו"ר, תאריך הישיבה', x='אחוז מסך המלים בפרוטוקול', title=f'שיעור השתתפות של היו"ר (בחלק הישיבה בה כיהן כיו"ר) בפרוטוקול ועדת חוקה', orientation='h',  category_orders={'index': t.index[::-1]}, color='יו"ר')
    fig.update_layout( yaxis={'categoryorder':'array', 'categoryarray':t['יו"ר, תאריך הישיבה']})
    fig.update_layout(title={'xanchor': 'center', 'x':0.5})
    fix_and_write(fig=fig,
                    filename="by_chairman_older_protocols_decending_order.png",
                    output_dir=config['output_dir'],
                    height_factor=1/2,
                    width_factor=1/2)

def split_chairperson():
    logger.info("extracting chairperson")
    d = Path(config['input_dir']) / "older meetings"
    for x in d.glob("*.xlsx"):
        if str(x).endswith("_processed.xlsx"):
            continue
        df = pd.read_excel(x)
        t = df.loc[df['name'].str.startswith("היו\"ר"), 'name']
        df['chairman_segment'] = (t.shift(1, fill_value=t.head(1)) != t).cumsum()
        df['chairman_segment'] = df['chairman_segment'].ffill()
        df['chairman'] = df['chairman_segment'].replace(df.groupby('chairman_segment')['name'].first().to_dict())
        df.to_excel(f"{str(x)[:-5]}_processed.xlsx")
    df1 = pd.read_excel(Path(config['input_dir']) / "protocols by order updated timestamp.xlsx")
    t = df1.loc[df1['name'].str.startswith("היו\"ר"), 'name']
    df1['chairman_segment'] = (t.shift(1, fill_value=t.head(1)) != t).cumsum()
    df1['chairman_segment'] = df1['chairman_segment'].ffill()
    df1['chairman'] = df1['chairman_segment'].replace(df1.groupby('chairman_segment')['name'].first().to_dict())
    df1.to_excel("21.1.23_processed.xlsx")

def main():
    split_chairperson()
    chairpersons()
    by_category_comparison()