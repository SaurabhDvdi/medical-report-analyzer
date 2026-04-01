import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import LabValue, Report, User
import os

class AnalyticsService:
    def __init__(self):
        self.charts_dir = "charts"
        os.makedirs(self.charts_dir, exist_ok=True)
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 6)
    
    def _get_lab_values_df(self, user_id: int, role: str, start_date: str = None, end_date: str = None, db: Session = None) -> pd.DataFrame:
        """Get lab values as pandas DataFrame"""
        query = db.query(LabValue).join(Report)
        
        if role != "doctor":
            query = query.filter(Report.user_id == user_id)
        
        if start_date:
            query = query.filter(Report.upload_date >= datetime.fromisoformat(start_date))
        
        if end_date:
            query = query.filter(Report.upload_date <= datetime.fromisoformat(end_date))
        
        lab_values = query.all()
        
        data = []
        for lv in lab_values:
            data.append({
                'parameter_name': lv.parameter_name,
                'value': lv.value,
                'unit': lv.unit,
                'reference_range': lv.reference_range,
                'is_abnormal': lv.is_abnormal,
                'date': lv.report.upload_date,
                'report_id': lv.report_id
            })
        
        return pd.DataFrame(data)
    
    def generate_trend_chart(self, parameter_name: str, user_id: int, role: str, 
                            start_date: str = None, end_date: str = None, db: Session = None) -> str:
        """Generate trend line chart for a parameter over time"""
        df = self._get_lab_values_df(user_id, role, start_date, end_date, db)
        
        if df.empty:
            # Create empty chart
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=14)
            ax.set_title(f'Trend: {parameter_name}')
        else:
            param_df = df[df['parameter_name'] == parameter_name].sort_values('date')
            
            if param_df.empty:
                fig, ax = plt.subplots()
                ax.text(0.5, 0.5, f'No data for {parameter_name}', ha='center', va='center', fontsize=14)
                ax.set_title(f'Trend: {parameter_name}')
            else:
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Plot values
                ax.plot(param_df['date'], param_df['value'], marker='o', linewidth=2, markersize=8, label='Value')
                
                # Highlight abnormal values
                abnormal = param_df[param_df['is_abnormal'] == True]
                if not abnormal.empty:
                    ax.scatter(abnormal['date'], abnormal['value'], color='red', s=100, 
                             zorder=5, label='Abnormal', marker='x')
                
                # Parse reference range if possible
                try:
                    ref_range = param_df['reference_range'].iloc[0]
                    if ref_range and '-' in ref_range:
                        parts = ref_range.split('-')
                        if len(parts) == 2:
                            lower = float(parts[0].strip())
                            upper = float(parts[1].strip())
                            ax.axhline(y=lower, color='green', linestyle='--', alpha=0.5, label='Lower Limit')
                            ax.axhline(y=upper, color='green', linestyle='--', alpha=0.5, label='Upper Limit')
                except:
                    pass
                
                ax.set_xlabel('Date')
                ax.set_ylabel(f'{parameter_name} ({param_df["unit"].iloc[0] if not param_df["unit"].empty else ""})')
                ax.set_title(f'Trend Analysis: {parameter_name}')
                ax.legend()
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()
        
        chart_path = os.path.join(self.charts_dir, f'trend_{parameter_name}_{datetime.now().timestamp()}.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def generate_comparison_chart(self, parameter_names: list, user_id: int, role: str, db: Session = None) -> str:
        """Generate bar chart comparing multiple parameters"""
        df = self._get_lab_values_df(user_id, role, None, None, db)
        
        if df.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=14)
            ax.set_title('Parameter Comparison')
        else:
            # Get latest values for each parameter
            latest_values = []
            for param in parameter_names:
                param_df = df[df['parameter_name'] == param]
                if not param_df.empty:
                    latest = param_df.sort_values('date').iloc[-1]
                    latest_values.append({
                        'parameter': param,
                        'value': latest['value'],
                        'unit': latest['unit'],
                        'is_abnormal': latest['is_abnormal']
                    })
            
            if latest_values:
                fig, ax = plt.subplots(figsize=(12, 6))
                params = [v['parameter'] for v in latest_values]
                values = [v['value'] for v in latest_values]
                colors = ['red' if v['is_abnormal'] else 'steelblue' for v in latest_values]
                
                bars = ax.bar(params, values, color=colors, alpha=0.7, edgecolor='black')
                ax.set_xlabel('Parameter')
                ax.set_ylabel('Value')
                ax.set_title('Parameter Comparison (Latest Values)')
                ax.grid(True, alpha=0.3, axis='y')
                
                # Add value labels on bars
                for bar, val in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{val:.2f}', ha='center', va='bottom')
                
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
            else:
                fig, ax = plt.subplots()
                ax.text(0.5, 0.5, 'No data for selected parameters', ha='center', va='center', fontsize=14)
                ax.set_title('Parameter Comparison')
        
        chart_path = os.path.join(self.charts_dir, f'comparison_{datetime.now().timestamp()}.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def generate_health_summary(self, user_id: int, role: str, db: Session = None) -> str:
        """Generate health summary visualization"""
        df = self._get_lab_values_df(user_id, role, None, None, db)
        
        if df.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=14)
            ax.set_title('Health Summary')
        else:
            # Count abnormal vs normal values
            abnormal_count = df['is_abnormal'].sum()
            normal_count = len(df) - abnormal_count
            
            # Get unique parameters
            unique_params = df['parameter_name'].unique()
            
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Pie chart for abnormal vs normal
            axes[0].pie([normal_count, abnormal_count], 
                       labels=['Normal', 'Abnormal'],
                       colors=['green', 'red'],
                       autopct='%1.1f%%',
                       startangle=90)
            axes[0].set_title('Overall Health Status')
            
            # Bar chart for abnormal parameters
            abnormal_params = df[df['is_abnormal'] == True]['parameter_name'].value_counts()
            if not abnormal_params.empty:
                axes[1].barh(abnormal_params.index, abnormal_params.values, color='red', alpha=0.7)
                axes[1].set_xlabel('Number of Abnormal Readings')
                axes[1].set_title('Most Frequently Abnormal Parameters')
            else:
                axes[1].text(0.5, 0.5, 'No abnormal values', ha='center', va='center', fontsize=12)
                axes[1].set_title('Most Frequently Abnormal Parameters')
            
            plt.tight_layout()
        
        chart_path = os.path.join(self.charts_dir, f'health_summary_{datetime.now().timestamp()}.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def generate_correlation_heatmap(self, user_id: int, role: str, db: Session = None) -> str:
        """Generate correlation heatmap for numeric parameters"""
        df = self._get_lab_values_df(user_id, role, None, None, db)
        
        if df.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=14)
            ax.set_title('Parameter Correlation')
        else:
            # Pivot to get parameters as columns
            pivot_df = df.pivot_table(
                index='report_id',
                columns='parameter_name',
                values='value',
                aggfunc='mean'
            )
            
            if pivot_df.shape[1] < 2:
                fig, ax = plt.subplots()
                ax.text(0.5, 0.5, 'Insufficient data for correlation', ha='center', va='center', fontsize=14)
                ax.set_title('Parameter Correlation')
            else:
                # Calculate correlation
                corr_matrix = pivot_df.corr()
                
                fig, ax = plt.subplots(figsize=(12, 10))
                sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                           center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8})
                ax.set_title('Parameter Correlation Heatmap')
                plt.tight_layout()
        
        chart_path = os.path.join(self.charts_dir, f'correlation_{datetime.now().timestamp()}.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return chart_path

