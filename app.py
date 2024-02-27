import streamlit as st
import requests
import xlrd
from bs4 import BeautifulSoup
import io
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd

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


## FUNGSI BOX PLOT
def box_plot(region_whr_df):
  plt.figure(figsize=(20, 12))
  sns.boxplot(data=region_whr_df, x='Sub-region', y='Ladder score', hue='Sub-region', width=0.5)
  plt.title('Distribusi indeks kebahagiaan berdasarkan Region', fontsize=18)
  plt.xlabel('Sub-region', fontsize=16)
  plt.ylabel('Indeks Kebahagiaan', fontsize=16)
  plt.xticks(rotation=90, fontsize=16)
  plt.subplots_adjust(bottom=1.0, top=1.5) # Menambahkan margin di bagian bawah

  # plt.legend(title='Sub-region', loc='center left', bbox_to_anchor=(1, 0.5))
  # Menambahkan garis putus-putus pada y = 6 dan y = 4.5
  plt.axhline(y=6, color='gray', linestyle='--')
  plt.axhline(y=4.5, color='gray', linestyle='--')
  st.set_option('deprecation.showPyplotGlobalUse', False)
  st.pyplot()


  ## FUNGSI GEOGRAFIS
def geografis(region_whr_df):
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    for_plotting = world.merge(region_whr_df, left_on='name', right_on='Country name')
    st.pyplot(
        for_plotting.plot(column='Ladder score', cmap='YlGnBu', figsize=(15, 10), k=3, legend=True,
                          legend_kwds={'label': "Happiness Score Per Country", 'orientation': "horizontal"},
                          edgecolor='gray',
                          missing_kwds={'color': 'lightgrey'}).get_figure()
    )
    
    
def scatter_plots(region_whr_df):
    x_columns = ['Social support', 'Logged GDP per capita',  'Healthy life expectancy']
    
    # Scatter plots for Ladder score vs other variables
    col1, col2, col3 = st.columns(3)
    for i, x_column in enumerate(x_columns):
        with col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3:
            plt.figure(figsize=(8, 6))
            sns.scatterplot(data=region_whr_df, x=x_column, y='Ladder score')
            plt.title(f'Scatter Plot of Ladder score vs {x_column}')
            plt.xlabel(x_column)
            plt.ylabel('Ladder score')
            plt.grid(True)
            st.set_option('deprecation.showPyplotGlobalUse', False)
            st.pyplot()

    # Scatter plots for variables against each other
    col1, col2, col3 = st.columns(3)
    k = 0
    for i in range(len(x_columns)):
        for j in range(i + 1, len(x_columns)):
            with col1 if k % 3 == 0 else col2 if k % 3 == 1 else col3:
                plt.figure(figsize=(8, 6))
                sns.scatterplot(data=region_whr_df, x=x_columns[i], y=x_columns[j])
                plt.title(f'Scatter Plot of {x_columns[i]} vs {x_columns[j]}')
                plt.xlabel(x_columns[i])
                plt.ylabel(x_columns[j])
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


## FUNGSI PERSENTASE BAHAGIA
def persentase_bahagia(region_whr_df):
    persentase_bahagia = {}
    for subreg in region_whr_df['Sub-region'].unique():
        subreg_df = region_whr_df[region_whr_df['Sub-region'] == subreg]
        
        total_records = len(subreg_df)
        
        bahagia_df = subreg_df[(subreg_df['Ladder score'] >= 6) & (subreg_df['Ladder score'] <= 8)]
        
        jumlah_bahagia = len(bahagia_df)
        
        if total_records != 0:
            persentase = round((jumlah_bahagia / total_records)*100 , 2) 
            persentase_bahagia[subreg] = persentase

    subreg_df = pd.DataFrame(list(persentase_bahagia.items()), columns=['Sub-regional', 'Persentase Bahagia'])
    subreg_df.sort_values(by='Persentase Bahagia', ascending=False, inplace=True)
    subreg_df['Persentase Bahagia'] = subreg_df['Persentase Bahagia'].astype(str) + '%'
    st.write("Negara-negara dengan indeks kebahagiaan (*ladder score*) lebih dari 6 dikategorikan sebagai negara berpenduduk bahagia.")
    st.write(subreg_df)


## FUNGSI RATA-RATA INDEKS KEBAHAGIAAN
def rata_rata_indeks_kebahagiaan(region_whr_df):
    condition =['Northern Europe', 'Western Europe',
          'Australia and New Zealand', 'Northern America']
    indicator = region_whr_df[['Sub-region','Ladder score',
          'Logged GDP per capita', 'Social support', 'Healthy life expectancy',
          'Freedom to make life choices', 'Generosity',
          'Perceptions of corruption']]
    filtered_data = indicator[indicator['Sub-region'].isin(condition)]
    # st.write(filtered_data.groupby('Sub-region').mean())
    st.write(filtered_data.groupby('Top Countries').mean())


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
             the UN Sustainable Development Solutions Network PBB, dan WHR Editorial Boad. Publikasi ini dibuat di bawah kendali 
             editorial Dewan Editorial WHR. World Happiness Report mencerminkan permintaan dunia untuk lebih memperhatikan 
             kebahagiaan dan kesejahteraan sebagai kriteria kebijakan pemerintah. Laporan ini mengulas keadaan kebahagiaan 
             di dunia saat ini dan menjelaskan variasi kebahagiaan pribadi dan nasional secara saintifik.""")
    st.write("""Tujuan dari menganalisis publikasi ini adalah untuk mengetahui bagaimana indeks kebahagiaan suatu negara yang 
             direpresentasikan oleh **ladder score** berhubungan dengan variabel-variabel seperti letak geografis, PDB per kapita, dukungan sosial, 
             harapan hidup sehat, kebebasan membuat pilihan dalam hidup, kemurahan hati, dan tingkat kepercayaan terhadap pemerintah. 
             Insights  yang diperoleh dari analisis publikasi ini diharapkan akan dapat membantu pemerintah dalam menentukan 
             kebijakan-kebijakan yang berorientasi ke arah peningkatan kebahagiaan masyarakat. Di bawah ini adalah dataset World 
             Happiness Report 2023.""")
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
        <p>Berikut ini adalah hipotesis yang diajukan: <br/>
            (H0) = Ada hubungan positif antara faktor geografis dan indeks kebahagiaan suatu negara. <br/>
            (Ha) = Tidak ada hubungan positif antara faktor geografis dan indeks kebahagiaan suatu negara. <br/>
        <p/>
    """, unsafe_allow_html=True)
    
##
def analisis_page():
    st.markdown("""
        <div style="text-align:center">
            <h2>Analisis Dataset World Happiness Report 2023</h2>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(['Peringkat   ', '   Distribusi   ','   Korelasi   ', '   Pembahasan dan Kesimpulan'])
    
    with tab1:
        st.markdown("""
            <div style="text-align:center">
                <h3>Peringkat Negara-negara Berdasarkan Indeks Kebahagiaan</h3>
            </div>
            """, unsafe_allow_html=True)
        st.write("""Negara-negara dengan <strong>indeks kebahagiaan mulai dari 6 ke atas</strong> dapat dikategorikan sebagai negara berpenduduk bahagia.""")
        bar_chart_country(region_whr_df)

        bar_chart_region(region_whr_df)

        st.markdown("""
            <p> Dari diagram di atas dapat diketahui bahwa: <br/>
                Terdapat 55 negara di seluruh dunia yang berpenduduk bahagia. <br/>
                29 negara dari benua Eropa (53%), <br/>
                13 negara dari benua Amerika (23.4%), <br/>
                11 negara dari benua Asia (20%), <br/>
                2 negara dari Oceania (3.6%), yaitu Australia dan New Zealand. <br/>
            </p>
        """, unsafe_allow_html=True)



    with tab2:
        st.markdown("""
        <div style="text-align:center">
            <h3>Analisis Distribusi Indeks kebahagiaan Negara-negara di Seluruh Dunia</h3>
        </div>
    """, unsafe_allow_html=True)
        
        geografis(region_whr_df)
        st.markdown("""
            <p>Berdasarkan peta geografis di atas, wilayah dengan warna gelap (indeks kebahagiaan tinggi) dapat ditemukan di
            belahan bumi selatan dan utara. <br/>
            Wilayah Oceania tampak bahagia secara menyeluruh. <br/>
            Wilayah Kanada tampak paling berbahagia di benua Amerika. <br/>
            Wilayah Eropa Utara tampak paling berbahagia di benua Eropa. <br/>
            Sebagian wilayah Asia Tengah tampak paling berbahagia di benua Asia. <br/><br/></p>
            """, unsafe_allow_html=True
        )

        box_plot(region_whr_df)
        st.markdown("""
            <p>Berdasarkan boxplot di atas, dapat di ketahui bahwa: </br>
                Semua negara di subregion Eropa Utara, Eropa Barat, Amerika Utara, dan "Australia dan New Zealand" berpenduduk bahagia. </br>
                Lebih dari 50% negara-negara di Eropa Timur, Eropa Selatan, dan "Amerika Selatan dan Karibia" berpenduduk bahagia. </br>
                Terdapat negara berpenduduk bahagia di semua subregion kecuali pada subregion-subregion yang berada di benua afrika. </br>  
            </p>
        """, unsafe_allow_html=True)
        
    with tab3:
         st.markdown("""
        <div style="text-align:center">
            <h3>Analisis Korelasi Matriks Prediktor terhadap Indeks Kebahagiaan</h3>
        </div>
    """, unsafe_allow_html=True)
         
         heatmap(region_whr_df)

         scatter_plots(region_whr_df)

         st.markdown("""
         <p>Berdasarkan heatmap dan scatterplot di atas, dapat diketahui bahwa <b>social support</b>, <b>GPA per Capita</b>, 
            dan <b>healthy life expectancy</b> mempunyai hubungan positif yang kuat (koefisien korelasi >= 7.0)terhadap <b>indeks kebahagiaan</b> dan
            ketiga matriks prediktor tersebut juga mempunyai hubungan positif yang kuat satu sama lain.
                         </p>
        <p>Singkatnya, indeks kebahagian suatu negara cenderung tinggi ketika indeks <b>social support</b>, <b>GPA per Capita</b>, 
        dan <b>healthy life expectancy</b> juga tinggi.<p/>
        """, unsafe_allow_html=True)
        
    with tab4:
        st.markdown("""
        <div style="text-align:center">
            <h3>Pembahasan dan Kesimpulan</h3>
        </div>
    """, unsafe_allow_html=True)
        st.markdown("""
        <p> Informasi yang tersirat dalam dataset World Happiness Report 2023 menunjukkan bahwa lebih dari 80% negara berpenduduk 
            bahagia di seluruh dunia menggunakan bahasa yang berasal dari benua Eropa. 
            Sebagai contoh, selain negara-negara Eropa, dari total 11 negara di Amerika Latin dan Karibia, 10 di antaranya menggunakan bahasa Spanyol, 
            sementara Brazil menggunakan bahasa Portugis. Di Asia Tenggara, negara seperti Singapura dan Malaysia menggunakan bahasa Inggris.
        </p>
    
        <p>Secara umum penduduk suatu negara merasa bahagia jika mereka hidup di lingkungan yang suportif, 
        sejahtera secara ekonomi, dan dalam keadaan sehat. Kesejahteraan ekonomi suatu negara berperan penting dalam menjaga 
        kesehatan penduduk suatu negara. Di samping itu, kondisi sosial yang suportif pada suatu negara akan 
        menjadikan penduduk negara itu lebih produktif dan produktifitas penduduk suatu negara akan berperan dalam pertumbuhan kesejahteraan ekonomi sautu negara.
        </p>
        <p> Negara-negara berpenduduk bahagia dapat ditemukan di berbagai belahan dunia terlepas dari perbedaan signifikan 
            terkait iklim, morfologi geografis, dan keanekaragaman hayati pada setiap wilayah. Dari fakta tersebut dapat diambil 
            kesimpulan bahwa faktor geografis tidak mempunyai hubungan positif terhadap indeks kebahagiaan negara-negara di seluruh 
            dunia. </p>
        <p>Ketiadaan negara berpenduduk bahagia di benua Afrika sebenarnya tidak berarti bertentangan dengan kesimpulan 
        pada bagian sebelumnya karena ternyata bagian utara Chile, bagian tenggara California, dan bagian barat daya Queensland 
        memiliki kemiripan morfologi geografis dengan wilayah-wilayah yang ada di benua Afrika tetapi semua wilayah itu 
        termasuk ke dalam wilayah negara-negara berpenduduk bahagia.
        </p>
        <p> Berdasarkan fakta di atas, saya menerima hipotesis alternatif yang menunjukkan bahwa tidak ada hubungan positif 
        antara faktor geografis dengan indeks kebahagian suatu negara. </p> 
        
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
            Berdasarkan hasil analisis sebelumnya yang menunjukkan bahwa kondisi sosial, ekonomi 
            dan kesehatan penduduk suatu negara berperan penting dalam menentukan tingkat kebahagiaan penduduk, maka 
            langkah-langkah konkret perlu dilaksanakan untuk meningkatkan kualitas aspek-aspek tersebut secara 
            menyeluruh dan merata dalam suatu negara.
        </p>
        <p>
            Salah satu upaya yang dapat dilakukan untuk meningkatkan kesejahteraan ekonomi adalah dengan meningkatkan
            pendapatan asli daerah, melalui peningkatan aktivitas ekonomi di setiap daerah sesuai dengan karakteristik
            masing-masing daerah dan penduduknya. 
        <p> Prinsip yang sama juga berlaku untuk meningkatkan kondisi sosial dan kesehatan masyarakat, yaitu dengan menggunakan pendekatan
            yang sesuai dengan karakteristik masing-masing daerah dan penduduknya.</p> 
        <p>
            Selain itu, perlu ditingkatkan studi banding dengan negara-negara yang memiliki tingkat kebahagiaan penduduk yang tinggi,
            sehingga pemerintah bisa memperoleh lebih banyak pengetahuan yang lebih aplikatif untuk diterapkan di Indonesia dalam upaya 
            meningkatkan indeks kebahagiaan masyarakat.
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








    
