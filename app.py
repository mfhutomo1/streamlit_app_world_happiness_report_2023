import streamlit as st
import requests
from bs4 import BeautifulSoup
import io
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import plotly.express as px
 

st.set_page_config(
    page_title="World Happiness Report 2023"
)

# membuat objek parser
html_page = requests.get("https://worldhappiness.report/data/")
soup = BeautifulSoup(html_page.content, "html.parser")

# membuat dataset1 WHR023
link_tag = soup.find("a", string="Data for Figure 2.1")
if link_tag:
    file_url = link_tag.get("href")
    if file_url:
        excel_response = requests.get(file_url)
        excel_data = excel_response.content
        whr_df = pd.DataFrame(pd.read_excel(io.BytesIO(excel_data)))
        whr_df = whr_df.sort_values(by='Ladder score', ascending=False)
    else:
        st.write("Tidak ada URL file Excel yang ditemukan.")
else:
    st.write("Tidak dapat menemukan link untuk file Excel.")

# dataset2 regional (pelengkap)
by_region_df = pd.read_csv('dataset_pelengkap/continents2.csv')
by_region_df = by_region_df[['name', 'alpha-2', 'region', 'sub-region']]
by_region_df.rename(columns={'name': 'Country name', 'alpha-2': 'Country code', 'region': 'Region', 'sub-region': 'Sub-region'}, inplace=True)

#merge dataset1 dan dataset2
region_whr_df = by_region_df.merge(whr_df, on= 'Country name', how = 'right')

# cleaning dataset
null_value = region_whr_df['Healthy life expectancy'].isnull()
zero_indices = region_whr_df[null_value].index
region_whr_df.loc[zero_indices, 'Healthy life expectancy'] = region_whr_df['Healthy life expectancy'].mean()

#fungsi dataset WHR2023
def dataset(region_whr_df):
    # menampilkan dataset
    def load_dataset(region):
        if region == 'All':
            return region_whr_df
        else:
            return region_whr_df[['Country name', 'Country code', 'Region', 'Sub-region', 'Ladder score',
          'Logged GDP per capita', 'Social support', 'Healthy life expectancy',
          'Freedom to make life choices', 'Generosity',
          'Perceptions of corruption']][region_whr_df['Region'] == region].sort_values(by=['Sub-region','Ladder score'], ascending=False).reset_index(drop=True)
    # tab untuk menampilkan dataset per region
    regions = ['All','Africa','Americas', 'Asia','Europe', 'Oceania' ]
    # Pilih tab
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(regions)
    # Isi konten untuk setiap tab
    with tab1:
        selected_dataset = load_dataset('All')
        st.write(selected_dataset)

    with tab2:
        selected_dataset = load_dataset('Africa')
        st.write(selected_dataset)

    with tab3:
        selected_dataset = load_dataset('Americas')
        st.write(selected_dataset)

    with tab4:
        selected_dataset = load_dataset('Asia')
        st.write(selected_dataset)

    with tab5:
        selected_dataset = load_dataset('Europe')
        st.write(selected_dataset)

    with tab6:
        selected_dataset = load_dataset('Oceania')
        st.write(selected_dataset)

# fungsi menampilkan peringkat negara-negara berdasarkan ladder score
def bar_chart_country(region_whr_df):
    # Define color palette
    subregion_palette = sns.color_palette("husl", len(region_whr_df["Sub-region"].unique()))
    subregion_color_map = {subregion: subregion_palette[i] for i, subregion in enumerate(region_whr_df["Sub-region"].unique())}
    # Set up streamlit sidebar
    country_list = region_whr_df["Region"].unique().tolist()
    country_list.insert(0, "All")
    select_region = st.selectbox('Filter the region here:', country_list)
    # Add ladder score slider
    score_range = st.slider('Adjust ladder score range:',
                            # min_value=region_whr_df["Ladder score"].min(),
                            # max_value=region_whr_df["Ladder score"].max(),
                            min_value=1.0, max_value=8.0,
                            # value=(region_whr_df["Ladder score"].min(), region_whr_df["Ladder score"].max()),
                            value=(6.0, 8.0),
                            step=0.5)
    # Apply filters
    if select_region == "All":
        filtered_df = region_whr_df[(region_whr_df["Ladder score"] >= score_range[0]) &
                                    (region_whr_df["Ladder score"] <= score_range[1])]
        # Plotting
        plt.figure(figsize=(30, 12))
        plt.bar(filtered_df["Country name"], filtered_df['Ladder score'], color='skyblue')
        plt.title('Indeks Kebahagiaan Negara-negara di Seluruh Dunia', fontsize=20)
        plt.xlabel('Nama Negara', fontsize=16)
        plt.ylabel('Indeks Kebahagiaan (Ladder Score)', fontsize=16)
        plt.xticks(rotation=90, fontsize=16)
        st.set_option('deprecation.showPyplotGlobalUse', False)
        st.pyplot()
    else:
        filtered_df = region_whr_df[(region_whr_df["Region"] == select_region) &
                                    (region_whr_df["Ladder score"] >= score_range[0]) &
                                    (region_whr_df["Ladder score"] <= score_range[1])]
        # Plotting
        plt.figure(figsize=(12, 6))
        bars = plt.bar(filtered_df["Country name"], filtered_df['Ladder score'], color=[subregion_color_map[subregion] for subregion in filtered_df["Sub-region"]])
        plt.title('Indeks Kebahagiaan Negara-negara di ' + select_region, fontsize=20)
        plt.xlabel('Nama Negara', fontsize=16)
        plt.ylabel('Indeks Kebahagiaan (Ladder Score)', fontsize=16)
        plt.xticks(rotation=90, fontsize=12)
        # Create legend manually
        legend_handles = []
        legend_labels = []
        for subregion in region_whr_df["Sub-region"].unique():
            legend_handles.append(plt.Rectangle((0,0),1,1, color=subregion_color_map[subregion]))
            legend_labels.append(subregion)
        plt.legend(legend_handles, legend_labels, title="Subregion", bbox_to_anchor=(1.05, 1), loc='upper left')
        st.set_option('deprecation.showPyplotGlobalUse', False)
        st.pyplot()
    # Display number of observations, updates dynamically
    number_of_results = filtered_df.shape[0]
    st.markdown(f'*Available Results: {number_of_results}*')
    st.markdown("---")


### FUNGSI BAR CHART
def bar_chart_region(region_whr_df):
    # Filter negara dengan Ladder score lebih dari atau sama dengan 6
    filtered_df = region_whr_df[region_whr_df['Ladder score'] >= 6]

    # Menghitung jumlah negara di setiap region
    region_counts = filtered_df['Region'].value_counts()

    # Plot diagram batang
    plt.figure(figsize=(6, 4))
    colors = plt.cm.tab10(range(len(region_counts)))  # Warna berbeda untuk setiap region
    bars = plt.bar(region_counts.index, region_counts.values, color=colors, width=0.3)

    # Menambahkan label jumlah negara di atas setiap bar
    for bar, count in zip(bars, region_counts.values ):
        plt.text(bar.get_x() + bar.get_width() / 2, 
                bar.get_height(), 
                count,
                ha='center', 
                va='bottom')
    # Menambahkan judul dan label sumbu
    plt.title('Jumlah Negara Berpenduduk Bahagia di Setiap Region', fontsize=12)
    plt.xlabel('Region', fontsize=9)
    plt.ylabel('Jumlah Negara', fontsize=9)
    # Menampilkan plot
    plt.subplots_adjust(bottom=0.5) # Menambahkan margin di bagian bawah
    plt.xticks(rotation=0, fontsize=8)  # Rotasi label sumbu x untuk memudahkan pembacaan
    plt.tight_layout()  # Mengatur layout agar tidak tumpang tindih
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()


def box_plot(region_whr_df):
    fig = px.box(region_whr_df, x='Sub-region', y='Ladder score', color='Sub-region',
                 title='Distribusi indeks kebahagiaan berdasarkan Region', 
                 labels={'Sub-region': 'Sub-region', 'Ladder score': 'Indeks Kebahagiaan'},
                 category_orders={"Sub-region": "hide"}
                 )

    fig.update_layout(xaxis_title='Sub-region', yaxis_title='Indeks Kebahagiaan', height=600, width=800)
    fig.update_traces(marker=dict(opacity=0.7), jitter=0.5, boxmean=True)  # Menyesuaikan properti plot
    fig.update_xaxes(tickangle=90, tickfont=dict(size=10))  # Merotasi label sumbu x
    fig.update_yaxes(tickfont=dict(size=16))  # Mengatur ukuran font di sumbu y

    fig.add_hline(y=6, line=dict(color='gray', dash='dash'))  # Menambahkan garis putus-putus pada y = 6
    fig.add_hline(y=4.5, line=dict(color='gray', dash='dash'))  # Menambahkan garis putus-putus pada y = 4.5

    fig.update_layout( xaxis=dict(title='', showticklabels=False))  # Menghilangkan label sub-region di sumbu x
    
    st.plotly_chart(fig, use_container_width=True)


# FUNGSI GEOGRAFIS
def geografis(region_whr_df):
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    # Mengganti 'United States' dengan 'United States of America'
    region_whr_df.loc[region_whr_df['Country name'] == 'United States', 'Country name'] = 'United States of America'
                             
    for_plotting = world.merge(region_whr_df, left_on='name', right_on='Country name')

    # Membuat peta interaktif dengan Plotly Express
    fig = px.choropleth(for_plotting,
                        title='Peta distribusi indeks kebahagiaan negara di seluruh dunia', 
                        locations='iso_a3', 
                        color='Ladder score', 
                        hover_name='Country name', 
                        color_continuous_scale='YlGnBu')
    
    title=dict(text='Distribusi indeks kebahagiaan berdasarkan Region',
                font=dict(size=20, color='black'), xanchor='center', y=0.1),  # Menyesuaikan posisi judul
    
    # Menampilkan peta menggunakan Streamlit
    st.plotly_chart(fig, use_container_width=True)

    
    
def scatter_plots(region_whr_df):

    st.markdown("""
        <h5 style='text-align: center;'> Scatter Plot Ladder score vs. Variable Indikator</h5>""", unsafe_allow_html=True
    )
    x_cols = ['Social support', 'Logged GDP per capita',  'Healthy life expectancy', 'Freedom to make life choices', 'Generosity', 'Perceptions of corruption']
    # Scatter plots for Ladder score vs other variables
    col1, col2, col3 = st.columns(3)
    for i, x_column in enumerate(x_cols):
        with col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3:
            plt.figure(figsize=(8, 6))
            sns.scatterplot(data=region_whr_df, x=x_column, y='Ladder score')
            plt.title(f'Indeks Kebahagiaan vs {x_column}')
            plt.xlabel(x_column)
            plt.ylabel('Indeks kebahagiaan')
            plt.grid(True)
            st.set_option('deprecation.showPyplotGlobalUse', False)
            st.pyplot()

    st.markdown("""
        <h5 style='text-align: center;'> Metriks Indikator yang Saling Berhubungan</h5>""", unsafe_allow_html=True)
    x_cols = ['Social support', 'Logged GDP per capita',  'Healthy life expectancy']
    # Scatter plots for variables against each other
    col1, col2, col3 = st.columns(3)
    k = 0
    for i in range(len(x_cols)):
        for j in range(i + 1, len(x_cols)):
            with col1 if k % 3 == 0 else col2 if k % 3 == 1 else col3:
                plt.figure(figsize=(8, 6))
                sns.scatterplot(data=region_whr_df, x=x_cols[i], y=x_cols[j])
                plt.title(f'Scatter Plot of {x_cols[i]} vs {x_cols[j]}')
                plt.xlabel(x_cols[i])
                plt.ylabel(x_cols[j])
                plt.grid(True)
                st.set_option('deprecation.showPyplotGlobalUse', False)
                st.pyplot()
            k += 1


## FUNGSI HEATMAP
def heatmap(region_whr_df):
  selected_columns = ['Ladder score','Logged GDP per capita', 'Social support', 'Healthy life expectancy', 
                      'Freedom to make life choices', 'Generosity', 'Perceptions of corruption']
  data_for_heatmap = region_whr_df[selected_columns]
  correlation_matrix = data_for_heatmap.corr()

  # Membuat heatmap
  plt.figure(figsize=(8, 6))
  sns.heatmap(correlation_matrix, annot=True, cmap='ocean', fmt=".2f")
  plt.title('Heatmap of Correlation Matrix')
  st.set_option('deprecation.showPyplotGlobalUse', False)
  st.pyplot()


#
def main():
    Pengantar, Dataset, Hipotesis, Analisis, Saran, Referensi = st.tabs(['Pengantar   ', 'Dataset   ', 'Hipotesis   ', 'Analisis   ', 'Saran   ', 'Referensi   '])
    
    with Pengantar:
        pengantar_page()

    with Dataset:
        dataset_page()

    with Hipotesis:
        hipotesis_page()

    with Analisis:
        analisis_page()
    
    with Saran:
        saran_page()

    with Referensi:
        referensi_page()


##
def pengantar_page():
    st.markdown("""
        <div style="text-align:center">
            <h2>World Happiness Report 2023</h2>
        </div>
    """, unsafe_allow_html=True)
    st.write("""World Happiness Report adalah sebuah publikasi yang diinisiasi oleh Gallup, Oxford Wellbeing Research Centre, 
             the UN Sustainable Development Solutions Network, dan WHR Editorial Board. Publikasi ini dibuat di bawah kendali 
             Dewan Editorial WHR. World Happiness Report mencerminkan permintaan dunia untuk lebih memperhatikan 
             kebahagiaan dan kesejahteraan sebagai kriteria kebijakan pemerintah. Laporan ini mengulas keadaan kebahagiaan 
             di dunia saat ini dan menjelaskan variasi kebahagiaan pribadi dan nasional secara saintifik.""")
    st.write("""Tujuan dari menganalisis publikasi ini adalah untuk mengetahui bagaimana indeks kebahagiaan suatu negara yang 
             direpresentasikan oleh **ladder score** berhubungan dengan variabel-variabel seperti letak geografis, PDB per kapita, dukungan sosial, 
             harapan hidup sehat, kebebasan membuat pilihan dalam hidup, kemurahan hati, dan tingkat kepercayaan terhadap pemerintah. 
             Insights  yang diperoleh dari analisis publikasi ini diharapkan akan dapat membantu pemerintah dalam menentukan 
             kebijakan-kebijakan yang berorientasi ke arah peningkatan kebahagiaan masyarakat.""")
##    
def dataset_page():
    st.markdown("""
        <div style="text-align:center">
            <h2>Dataset World Happiness Report 2023</h2>
        </div>
    """, unsafe_allow_html=True)
    dataset(region_whr_df)
    st.markdown("""Informasi mengenai bagaimana Gallup World Poll memperoleh setiap nilai yang ada pada dataset di atas, 
                tersedia selengkapnya [di sini](https://happiness-report.s3.amazonaws.com/2023/WHR+23_Statistical_Appendix.pdf 
                'Statistical Appendix of World Happiness Report 2023').""")
   
##
def hipotesis_page():
    st.markdown("""
        <div style="text-align:center">
            <h2>Hipotesis</h2>
        </div>
        <p>Berikut ini adalah hipotesis yang diajukan, <br/>
            (H0): <br/>
                   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                   Ada hubungan antara faktor geografis dan indeks kebahagiaan suatu negara
                   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                   Ada lebih dari satu faktor yang memengaruhi indeks kebahagiaan suatu negara. <br/>
            (Ha): <br/>
                   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                   Tidak ada hubungan antara faktor geografis dan indeks kebahagiaan suatu negara
                   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                   Hanya ada satu faktor yang memengaruhi indeks kebahagiaan suatu negara.
        <p/>
    """, unsafe_allow_html=True)
    
##
def analisis_page():
    st.markdown("""
        <div style="text-align:center">
            <h2>Analisis Dataset World Happiness Report 2023</h2>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(['Peringkat   ', '   Distribusi   ','   Korelasi   ', '   Kesimpulan'])
    
    with tab1:
        st.markdown("""
            <div style="text-align:center">
                <h3>Peringkat Negara-negara Berdasarkan Indeks Kebahagiaan</h3>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("""
            <p>Negara-negara dengan <b>indeks kebahagiaan mulai dari 6 ke atas</b> dapat dikategorikan sebagai negara berpenduduk bahagia</p>
        """, unsafe_allow_html=True)
        
        bar_chart_country(region_whr_df)

        bar_chart_region(region_whr_df)

        st.markdown("""
            <h6 style='text-align: center;'>Pembahasan</h6>""", unsafe_allow_html=True
        )
       
        st.markdown("""     
           <ul>Dari diagram di atas dapat diketahui bahwa:
                <li>Terdapat 55 negara di seluruh dunia yang berpenduduk bahagia versi World Happiness Report.</li>
                <li>29 negara dari benua Eropa (53%),</li>
                <li>13 negara dari benua Amerika (23.4%),</li>
                <li>11 negara dari benua Asia (20%),</li>
                <li>2 negara dari Oceania (3.6%), dan</li>
                <li>0 negara dari benua Afrika.</li>
                <li>
                    <ul>Informasi di atas menyiratkan bahwa lebih dari 80% negara berpenduduk bahagia menggunakan bahasa yang berasal dari benua Eropa.
                    Alasannya sebagai berikut:
                    <li><p>10 dari 11 negara berpenduduk bahagia di Amerika Latin dan Karibia yang disurvey oleh Gallup World Poll menggunakan bahasa Spanyol, sementara Brazil menggunakan bahasa Portugis.</p></li>
                    <li><p>Negara-negara bagian di Amerika Utara seperti Quebec dan Louisiana menggunakan bahasa Prancis selain bahasa Inggris.</p></li>
                    <li><p>Australia dan New Zealand menggunakan bahasa Inggris selain bahasa Aborigin atau Maori.</p></li>
                    <li><p>Di Asia Tenggara, negara seperti Singapura dan Malaysia menggunakan bahasa Inggris selain bahasa Melayu atau Mandarin.</p></li>
                    </ul> 
                </li>
                
            </ul>

           

        """, unsafe_allow_html=True)



    with tab2:
        
        geografis(region_whr_df)
        st.markdown("""
            <h6 style='text-align: center;'>Pembahasan</h6>""", unsafe_allow_html=True
        )
        st.markdown("""
            <p>Berdasarkan peta geografis di atas dapat diketahui bahwa wilayah berwarna biru tua, yang mengindikasikan wilayah berpenduduk bahagia, dapat ditemukan di berbagai belahan bumi dengan iklim yang beragam.</li>
            <p>Selanjutnya untuk mengetahui hubungan antara letak geografis dengan tingkat kebahagiaan penduduk, dilakukan pembagian wilayah berdasarkan garis lintang sehingga terbentuk lima grup wilayah dengan rentang sudut lintang yang berbeda.</p>
            <li> Wilayah pertama mencakup Finlandia</li>
            <li> Wilayah kedua mencakup Spanyol</li>
            <li> Wilayah ketiga mencakup Saudi Arabia</li>
            <li> Wilayah keempat mencakup Malaysia</li>
            <li> Wilayah kelima mencakup New Zealand</li>
            <ul>Kemudian informasi tambahan dari https://chat.openai.com di bawah ini disajikan untuk membantu proses analisis.
            <li> Sebagian besar wilayah Finlandia memiliki iklim <b>kontinental</b> dengan musim dingin yang sangat dingin dengan salju melimpah, serta musim panas yang hangat dan lembap. Matahari muncul sepanjang hari di musim panas dan hanya beberapa jam sehari di musim dingin.</li>
            <li> Spanyol memiliki iklim yang bervariasi, mulai dari <b>subtropis</b> di selatan hingga iklim <b>mediterania</b>, ditandai dengan musim dingin yang ringan serta musim panas yang panas dan kering, kemunculan matahari hingga 8 jam di musim dingin.</li>
            <li> Saudi Arabia memiliki iklim <b>gurun</b> yang panas dan kering, ditandai dengan matahari yang bersinar terang sepanjang tahun.</li>
            <li> Malaysia memiliki iklim <b>tropis</b> dengan sebagian besar wilayahnya berupa dataran rendah yang hangat dan lembab, sementara sebagian kecilnya merupakan pegunungan yang lebih sejuk. Matahari bersinar sepanjang tahun.</li>
            <li> New Zealand memiliki iklim yang bervariasi, mulai dari <b>subtropis</b> hingga <b>sub-antarctic</b>, dengan musim panas yang hangat dan musim dingin yang disertai salju, serta matahari yang sering muncul sepanjang tahun.</li>
            </ul>
            
            """, unsafe_allow_html=True
        )

        box_plot(region_whr_df)
        st.markdown("""
            <h6 style='text-align: center;'>Pembahasan</h6>""", unsafe_allow_html=True
        )
        st.markdown("""
            <ul>Berdasarkan boxplot di atas, dapat di ketahui bahwa: 
                <li> Semua negara yang disurvey oleh Gallup World Poll di subregion Eropa Utara, Eropa Barat, Amerika Utara, dan "Australia dan New Zealand" berpenduduk bahagia. </li>
                <li> Lebih dari 50% negara-negara di Eropa Timur, Eropa Selatan, dan "Amerika Selatan dan Karibia" berpenduduk bahagia. </li>
                <li> Terdapat negara berpenduduk bahagia di semua subregion kecuali pada subregion-subregion yang berada di benua afrika. </li>  
                <li> Terdapat 6 negara di sub-sahara Afrika yang memiliki indeks kebahagiaan di atas 5,
                  yang mana 5 dari 6 negara sub-sahara Afrika tersebut menggunakan bahasa Prancis selain bahasa asli mereka. Sementara itu,
                  hanya satu negara di Afrika Utara yang memiliki indeks kebahagiaan lebih dari 5.</li>
                <li> Negara paling bahagia versi World Happiness Report di benua Afrika adalah Mauritius yang berada di samudra hindia bukan
                  negara lain di Afrika Utara yang berbatasan dengan benua Eropa.</li>
            </ul>
        """, unsafe_allow_html=True)
        
    with tab3:
         st.markdown("""
        <div style="text-align:center">
            <h3>Analisis Korelasi Metriks Prediktor terhadap Indeks Kebahagiaan</h3>
        </div>
    """, unsafe_allow_html=True)
         
         heatmap(region_whr_df)

         scatter_plots(region_whr_df)
         st.markdown("""
            <h6 style='text-align: center;'>Pembahasan</h6>""", unsafe_allow_html=True
        )
         st.markdown("""
         <ul>Berdasarkan heatmap dan scatterplot di atas, dapat diketahui bahwa: 
            <li><b>Social support</b>, <b>GPA per Capita</b>, dan <b>healthy life expectancy</b> mempunyai hubungan positif yang kuat 
            terhadap <b>indeks kebahagiaan</b> dan ketiga metriks prediktor tersebut juga mempunyai 
            hubungan positif yang kuat satu sama lain. (koefisien korelasi >= 0.7)</li>
            <li><b>freedom to make life choices</b> mempunyai hubungan positif moderat atau cukup kuat terhadap 
            <b>indeks kebahagiaan</b>. (koefisien korelasinya 0.66)</li>
            <li><b>Generosity</b> tidak mempunyai hubungan terhadap <b>indeks kebahagiaan</b>. (koefisien korelasinya 0.04)</li>
            <li><b>Perception of corruption</b> mempunyai hubungan negatif yang moderat terhadap <b>indeks kebahagiaan</b>.
            (koefisien korelasinya -0.47)</li>
        </ul>
        
        """, unsafe_allow_html=True)
        
    with tab4:
        st.markdown("""
        <div style="text-align:center">
            <h3>Kesimpulan</h3>
        </div>
    """, unsafe_allow_html=True)
        st.markdown("""
        <p>Berdasarkan informasi dari halaman peringkat, dapat diajukan hipotesis baru sebagai berikut: <br/> "kebudayaan yang ada di suatu negara memengaruhi 
            indeks kebahagiaan penduduk suatu negara". <br/>Alasannya karena komunitas-komunitas yang akar budayanya berasal dari Eropa 
            cenderung mempunyai indeks kebahagiaan tinggi, seperti komunitas-komunitas yang membentuk negara  
            Australia, New Zealand, Amerika serikat, Kanada, beberapa negara di Amerika Latin, dll. <br/>
            Keberadaan budaya Eropa salah satunya ditandai dengan penggunaan bahasa Eropa oleh keturunan etnis Eropa di wilayah tersebut. </p>      
        <p>
        <ul>Berdasarkan informasi dari halaman distribusi, disimpulkan bahwa
            <li>Negara-negara berpenduduk bahagia dapat ditemukan di berbagai belahan dunia terlepas dari perbedaan signifikan terkait iklim, 
            dan topografi pada setiap wilayah. Dari fakta tersebut dapat diambil kesimpulan bahwa faktor geografis 
            tidak mempunyai hubungan positif terhadap indeks kebahagiaan negara-negara di seluruh dunia.
            </li>
            <li>
            Oleh karena itu, saya menerima hipotesis alternatif yang menyatakan bahwa tidak ada hubungan positif 
            antara faktor geografis dengan indeks kebahagian suatu negara. 
            </li>
        </ul>
                  
        <ul>Berdasarkan halaman korelasi, diambil kesimpulan bahwa 
            <li> Secara umum orang-orang merasa bahagia jika mereka hidup di lingkungan yang suportif, 
            sejahtera secara ekonomi, dan dalam keadaan sehat.Orang-orang juga merasa bahagia jika mereka diberi kebebasan untuk 
            membuat keputusan dalam hidup mereka sendiri. 
            </li>
            <li> Kesejahteraan ekonomi suatu negara berperan penting dalam menjaga 
            kesehatan penduduk suatu negara. Di samping itu, kondisi sosial yang suportif pada suatu negara akan 
            menjadikan penduduk negara itu lebih produktif dan produktifitas penduduk suatu negara akan berperan dalam 
            pertumbuhan kesejahteraan ekonomi suatu negara. 
            </li>
            <li>Tindak pidana korupsi yang terjadi di pemerintahan dan bisnis secara umum cenderung membuat masyarakat tidak bahagia</li>
            </li> Oleh karena itu, saya menerima hipotesis nol yang menyatakan bahwa ada
            lebih dari satu faktor yang memengaruhi indeks kebahagian penduduk suatu negara. 
            <li>
        </ul>
                    
        
        
        
    """, unsafe_allow_html=True)   
##    
def saran_page():
    st.markdown("""
        <div style="text-align:center">
            <h2>Saran</h2>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
                
        <p>
            Langkah-langkah konkret perlu dijalankan untuk meningkatkan kondisi sosial, ekonomi 
            dan kesehatan secara menyeluruh dan merata dalam suatu negara.
        </p>
        <p>
            Aktivitas ekonomi di setiap desa perlu ditingkatkan untuk untuk mengurangi tingkat pengangguran 
            dan menaikkan pendapatan asli daerah.
        </p>
        <p>
            Program penyuluhan tentang pentingnya hidup sehat dan cara-cara hidup sehat, serta pentingnya
            mewujudkan lingkungan yang suportif dan cara-cara mewujudkannya, perlu di selenggarakan secara
            berkelanjutan.
        </p> 
        
        <p>
            Toleransi perlu dikembangkan agar setiap individu dalam suatu komunitas tidak merasa terikat secara personal
            dengan nilai-nilai adat yang kadang kala membatasi seseorang dalam menentukan pilihan hidupnya.
        </p>
                
        <p>
            Walaupun generosity tidak berhubungan dengan tingkat kebahagiaan secara langsung, tetapi budaya generous
            harus dikembangkan sebagai upaya menciptakan lingkungan yang suportif, yang akan berdampak terhadap 
            tingkat kebahagiaan pada akhirnya</p>
        <p>
            Studi banding dengan negara-negara yang memiliki tingkat kebahagiaan penduduk yang tinggi perlu ditingkatkan,
            sehingga pemerintah suatu negara bisa memperoleh lebih banyak pengetahuan yang lebih aplikatif untuk diterapkan 
            dalam upaya meningkatkan indeks kebahagiaan masyarakat.
        </p>
    """, unsafe_allow_html=True)
##
def referensi_page():
    st.title('Referensi')
    st.write('[Tentang World Happiness Report](https://worldhappiness.report/about/)')
    st.write('[Tentang metode penelitian dan pengumpulan data](https://www.youtube.com/watch?v=VMbaOcyDtsQ)')
    st.write('[Tentang dataset World Happiness Report](https://worldhappiness.report/data/)')
    st.write('[Tentang dataset geografis pelengkap](https://www.kaggle.com/datasets/deepthi21/continents2)')


if __name__ == '__main__':
    main()








    
