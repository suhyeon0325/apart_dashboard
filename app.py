# -*- coding:utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px 
import geopandas as gpd
import contextily as ctx
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import math
import matplotlib.pyplot as plt
import xyzservices.providers as xyz
import plotly.io as pio
from plotly.subplots import make_subplots

load_dotenv()
MAP_TOKEN = os.getenv('MAP_TOKEN')

st.set_page_config(
    page_title="메인",
    page_icon=None,  # 아이콘 없음
    layout="wide", 
    initial_sidebar_state="expanded"
    )

# st.cache_data를 사용하여 GeoJSON 데이터를 캐싱합니다.
@st.cache_data
def load_geo_data(geojson_file):
    gdf = gpd.read_file(geojson_file)
    return gdf

@st.cache_data
def load_data(csv_file):
    data = pd.read_csv(csv_file)
    return data



def main():
    # 대시보드 제목
    st.title("서울특별시 아파트 매매 거래 지역별 정보")
    st.divider()
    
    # 데이터 불러오기
    geo_data = load_geo_data("data/seoul_jan.geojson")
    data = load_data("data/data.csv")   


    col1, col2 = st.columns([7,3])
    
    with col1: 
        with st.container(border=True, height=600):
            st.subheader("1월 서울특별시 시군구별 아파트 매매 지도", divider='blue', help='건물 면적이 커질수록 원의 크기도 상대적으로 커집니다.')
            
            # 자치구별로 그룹화
            geo_data = geo_data.set_crs(epsg=4326, allow_override=True)

            # 경도 위도 추가
            geo_data["lon"] = geo_data.geometry.centroid.x
            geo_data["lat"] = geo_data.geometry.centroid.y

            # 소수점 둘째자리까지
            geo_data['평균_물건금액'] = geo_data['평균_물건금액'].round(2)
            geo_data['평균_건물면적'] = geo_data['평균_건물면적'].round(2)
            geo_data['평균_건축년도'] = geo_data['평균_건축년도'].round(2)

            # hover 생성
            geo_data['hover_text'] = geo_data['자치구명'] + '<br>' + \
                                    '평균 물건 금액: ' + geo_data['평균_물건금액'].astype(str) + '<br>' + \
                                    '평균 건물 면적: ' + geo_data['평균_건물면적'].astype(str) + '<br>' + \
                                    '평균 건축년도: ' + geo_data['평균_건축년도'].astype(str)                                     

            # 플롯 생성하기
            fig = px.scatter_mapbox(
                geo_data,
                lat="lat",
                lon="lon",
                color="평균_물건금액",
                size="평균_건물면적",
                hover_name="자치구명",
                hover_data={
                    "hover_text": True,
                    "lat": False,
                    "lon": False,
                    "자치구명": False,
                    "평균_물건금액": False, 
                    "평균_건물면적": False,
                    "평균_건축년도": False,
                    },
                color_continuous_scale="Portland",
                size_max=30,
                zoom=10,
                mapbox_style="light"
            )

            # 레이아웃 설정하기
            fig.update_layout(
                margin={"r":0, "t":0, "l":0, "b":0},
                mapbox=dict(
                    accesstoken=MAP_TOKEN,  
                    bearing=0,
                    center=dict(
                        lat=geo_data["lat"].mean(),
                        lon=geo_data["lon"].mean()
                    ),
                    pitch=0,
                    zoom=10
                )
            )

            # Display the figure in the Streamlit app
            st.plotly_chart(fig)
            
    with col2:
        with st.container(border=False, height=600):
            with st.container(border=True, height=138):
                st.metric(label="1월 총 거래 건수", value='3112건', delta= '-34.08% (23년 12월 대비)',
                        delta_color="normal", help="미접수 거래는 반영되지 않았습니다.")
            with st.container(border=True, height=138):
                st.metric(label="1월 최다 거래 지역", value='강서구', delta='평균 대비 112건',
                        delta_color="normal", help="강서구의 1월 거래량은 총 236건입니다.")
            with st.container(border=True, height=138):
                st.metric(label="1월 최고 거래가 지역", value='강남구', delta='평균 대비 119,382만원',
                        delta_color="normal", help="강남구의 1월 평균 거래가는 158,170만원입니다.")
            with st.container(border=True, height=138):
                st.metric(label="1월 건물면적(㎡) 넓은 지역", value='성동구', delta='평균 대비 24.57㎡',
                        delta_color="normal", help="성동구의 1월 평균 건물면적은 84.75㎡입니다.")
        
    
    with st.container(border=True):
        st.subheader('아파트 매매 데이터 지역별 비교')
        col3, col4, col5 = st.columns([3,3,4])
        
        with col3: 
            with st.container(border=True, height=215):
                # 첫 번째 구 선택
                district_list = data['자치구명'].unique()
                selected_district1 = st.selectbox('첫 번째 지역의 구를 선택하세요:', district_list)
                # 선택된 구 내의 동 선택
                dong_list1 = data[data['자치구명'] == selected_district1]['법정동명'].unique()
                selected_dong1 = st.selectbox(f'{selected_district1}의 동을 선택하세요:', dong_list1)

        with col4: 
            with st.container(border=True, height=215):
                # 두 번째 구 선택
                selected_district2 = st.selectbox('두 번째 지역의 구를 선택하세요:', district_list, index=(0 if selected_district1 not in district_list else district_list.tolist().index(selected_district1)))
                # 선택된 구 내의 동 선택
                dong_list2 = data[data['자치구명'] == selected_district2]['법정동명'].unique()
                if selected_district1 == selected_district2:
                    dong_list2 = [dong for dong in dong_list2 if dong != selected_dong1]  # 첫 번째 선택된 '동' 제외
                selected_dong2 = st.selectbox(f'{selected_district2}의 동을 선택하세요:', dong_list2)

        with col5: 
            with st.container(border=True, height=215):
                # 계약일이 문자열 형식이라면 datetime 형식으로 변환
                if data['계약일'].dtype != 'datetime64[ns]':
                    data['계약일'] = pd.to_datetime(data['계약일'], format='%Y%m%d')

                # 계약일의 최소값과 최대값을 datetime 형식으로 구함
                min_date = data['계약일'].min().to_pydatetime()
                max_date = data['계약일'].max().to_pydatetime()

                # 계약일 슬라이더
                selected_dates = st.slider('계약일을 선택하세요:',
                                        min_value=min_date, 
                                        max_value=max_date, 
                                        value=(min_date, max_date),
                                        format="YYYY-MM-DD")  # 슬라이더에서 날짜를 어떻게 표시할지 지정

                # 건축년도 슬라이더
                min_year_built = int(data[data['건축년도'] != 0]['건축년도'].min())
                max_year_built = int(data['건축년도'].max())                

                selected_year_built = st.slider('건축년도를 선택하세요:', min_value=min_year_built, max_value=max_year_built, value=(min_year_built, max_year_built))

                # 필터링된 데이터 생성
                filtered_df1 = data[
                    (data['자치구명'] == selected_district1) & 
                    (data['법정동명'] == selected_dong1) & 
                    (data['계약일'] >= selected_dates[0]) & 
                    (data['계약일'] <= selected_dates[1]) & 
                    (data['건축년도'] >= selected_year_built[0]) & 
                    (data['건축년도'] <= selected_year_built[1])
                ]

                filtered_df2 = data[
                    (data['자치구명'] == selected_district2) & 
                    (data['법정동명'] == selected_dong2) & 
                    (data['계약일'] >= selected_dates[0]) & 
                    (data['계약일'] <= selected_dates[1]) & 
                    (data['건축년도'] >= selected_year_built[0]) & 
                    (data['건축년도'] <= selected_year_built[1])
                ]


    # 데이터 시각화
    with st.container(border=True, height=800):
        # 계약일에 따른 전체 데이터 필터링
        filtered_data = data[
        (data['계약일'] >= selected_dates[0]) & 
        (data['계약일'] <= selected_dates[1]) &
        (data['건축년도'] >= selected_year_built[0]) & 
        (data['건축년도'] <= selected_year_built[1])
    ]
        tab1, tab2, tab3, tab4 = st.tabs(["가격 추이", "거래량 추이", "거래 금액 비교", "상관관계 분석"])

        # 가격 추이 탭
        with tab1:
            # 각 데이터셋에 대해 계약일별 평균 '물건금액(만원)'을 계산
            avg_price_over_time_df1 = filtered_df1.groupby('계약일')['물건금액(만원)'].mean().reset_index()
            avg_price_over_time_df2 = filtered_df2.groupby('계약일')['물건금액(만원)'].mean().reset_index()
            avg_price_over_time_data = filtered_data.groupby('계약일')['물건금액(만원)'].mean().reset_index()
            # 선 그래프를 생성
            fig = go.Figure()

            # 첫 번째 필터링된 데이터에 대한 선 그래프 추가
            fig.add_trace(go.Scatter(x=avg_price_over_time_df1['계약일'], y=avg_price_over_time_df1['물건금액(만원)'],
                                mode='lines',
                                name=f'{selected_district1} {selected_dong1}',
                                line=dict(color='#557FFF')))

            # 두 번째 필터링된 데이터에 대한 선 그래프 추가
            fig.add_trace(go.Scatter(x=avg_price_over_time_df2['계약일'], y=avg_price_over_time_df2['물건금액(만원)'],
                                mode='lines',
                                name=f'{selected_district2} {selected_dong2}',
                                line=dict(color='#04CA96')))

            # 전체 데이터에 대한 선 그래프 추가
            fig.add_trace(go.Scatter(x=avg_price_over_time_data['계약일'], y=avg_price_over_time_data['물건금액(만원)'],
                                mode='lines',
                                name='전체 데이터',
                                line=dict(color='#F94B60')))

            # 그래프 레이아웃 설정
            fig.update_layout(
                title=f'{selected_dong1} VS  {selected_dong2}의 평균 가격 추이',
                xaxis_title='계약일',
                yaxis_title='평균 물건금액(만원)',
                hovermode="x",
                width=1200,  
                height=600  
            )

        
            st.plotly_chart(fig)

        # 거래량 추이 탭    
        with tab2:
            # 전체 데이터에서 계약일별 각 동의 거래 건수 계산
            transaction_count_over_time_per_dong = filtered_data.groupby(['계약일', '법정동명']).size().reset_index(name='거래 건수')

            # 모든 동에 대해 계약일별 평균 거래량 계산
            avg_transaction_count_over_time = transaction_count_over_time_per_dong.groupby('계약일')['거래 건수'].mean().reset_index()

            fig = go.Figure()

            # filtered_df1의 거래량 추이에 대한 선 그래프 추가
            transaction_count_over_time_df1 = filtered_df1.groupby('계약일').size().reset_index(name='거래 건수')
            fig.add_trace(go.Scatter(
                x=transaction_count_over_time_df1['계약일'], 
                y=transaction_count_over_time_df1['거래 건수'],
                mode='lines',
                name=f'{selected_district1} {selected_dong1}',
                line=dict(color='#557FFF')
            ))

            # filtered_df2의 거래량 추이에 대한 선 그래프 추가
            transaction_count_over_time_df2 = filtered_df2.groupby('계약일').size().reset_index(name='거래 건수')
            fig.add_trace(go.Scatter(
                x=transaction_count_over_time_df2['계약일'], 
                y=transaction_count_over_time_df2['거래 건수'],
                mode='lines',
                name=f'{selected_district2} {selected_dong2}',
                line=dict(color='#04CA96')
            ))

            # 모든 동의 평균 거래량 추이에 대한 선 그래프 추가
            fig.add_trace(go.Scatter(
                x=avg_transaction_count_over_time['계약일'], 
                y=avg_transaction_count_over_time['거래 건수'],
                mode='lines',
                name='전체 동 평균 거래량',
                line=dict(color='#F94B60'))
            )

            # 그래프 레이아웃 설정
            fig.update_layout(
                title=f'{selected_dong1} VS  {selected_dong2}의 거래량 추이',
                xaxis_title='계약일',
                yaxis_title='거래 건수',
                hovermode="x",
                width=1200, 
                height=600  
            )

            # 그래프 표시
            st.plotly_chart(fig)

        # 거래금액 비교 탭
        with tab3:
            
            # 박스 플롯을 생성
            fig = go.Figure()

            # 첫 번째 필터링된 데이터에 대한 박스 플롯 추가
            fig.add_trace(go.Box(
                y=filtered_df1['물건금액(만원)'],
                name=f'{selected_district1} {selected_dong1}',
                boxpoints='outliers',  
                jitter=0.3,  
                marker_color='#557FFF'
                ))

            # 두 번째 필터링된 데이터에 대한 박스 플롯 추가
            fig.add_trace(go.Box(
                y=filtered_df2['물건금액(만원)'],
                name=f'{selected_district2} {selected_dong2}',
                boxpoints='outliers', 
                jitter=0.3,  
                marker_color='#04CA96'
                ))

            # 레이아웃 설정
            fig.update_layout(
                title=f'{selected_dong1} VS  {selected_dong2}의 거래 금액 비교',
                yaxis_title='물건금액(만원)',
                boxmode='group',  
                width=1000,  
                height=700   
            )

            # 그래프 표시
            st.plotly_chart(fig)


        # 상관관계 분석 탭
        with tab4:
            # 관심 있는 변수 선택
            columns_of_interest = ['건물면적(㎡)', '층', '건축년도', '물건금액(만원)']

            # 선택된 동의 데이터에서 관심 있는 변수만 추출
            data_of_interest_df1 = filtered_df1[columns_of_interest]
            data_of_interest_df2 = filtered_df2[columns_of_interest]

            # 상관 관계 행렬 계산
            correlation_matrix_df1 = data_of_interest_df1.corr()
            correlation_matrix_df2 = data_of_interest_df2.corr()

            # 두 개의 히트맵을 위한 subplot 설정
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=(f'{selected_district1} {selected_dong1} 상관 관계', f'{selected_district2} {selected_dong2} 상관 관계')
            )

            # 첫 번째 선택된 동의 히트맵
            heatmap1 = go.Heatmap(
                z=correlation_matrix_df1.values,
                x=correlation_matrix_df1.columns,
                y=correlation_matrix_df1.index,
                colorscale='RdBu',
                zmid=0
            )
            fig.add_trace(heatmap1, row=1, col=1)

            # 두 번째 선택된 동의 히트맵
            heatmap2 = go.Heatmap(
                z=correlation_matrix_df2.values,
                x=correlation_matrix_df2.columns,
                y=correlation_matrix_df2.index,
                colorscale='RdBu',
                zmid=0
            )
            fig.add_trace(heatmap2, row=1, col=2)

            # 레이아웃 업데이트
            fig.update_layout(title_text='변수 간 상관 관계 비교', width=1200, height=600)

            st.plotly_chart(fig)
            expander = st.expander("히트맵 설명보기")
            expander.write(f'''
                이 히트맵은 {selected_district1} {selected_dong1}과 {selected_district2} {selected_dong2} 지역의 주요 부동산 관련 변수들 사이의 상관 관계를 시각적으로 나타냅니다. 
                빨간색에 가까울수록 한 변수의 값이 증가할 때 다른 변수의 값도 증가하는 경향이 있습니다.
                파란색에 가까울수록 한 변수의 값이 증가할 때 다른 변수의 값은 감소하는 경향이 있습니다.
                흰색에 가까울수록 거의 또는 전혀 상관관계가 없음을 의미합니다.
            ''')

if __name__ == "__main__":
    main()

