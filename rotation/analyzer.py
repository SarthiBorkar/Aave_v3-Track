"""
Data Analysis Module for USDC Supply Events
"""

import pandas as pd
from typing import List, Dict, Tuple
from datetime import datetime
from aave_usdc_analysis.config import OUTPUT_CSV, SUMMARY_CSV


class SupplyEventAnalyzer:
    """Analyzes USDC supply events and generates insights"""
    
    def __init__(self, events: List[Dict]):
        """
        Initialize analyzer with events
        
        Args:
            events: List of parsed supply event dictionaries
        """
        self.events = events
        self.df = pd.DataFrame(events)
        
        # Convert timestamp to datetime if available
        if 'timestamp' in self.df.columns and self.df['timestamp'].sum() > 0:
            self.df['datetime'] = pd.to_datetime(self.df['timestamp'], unit='s')
    
    def analyze(self) -> Dict:
        """
        Perform comprehensive analysis of supply events
        
        Returns:
            Dictionary containing analysis results
        """
        print("\n" + "="*60)
        print("AAVE V3 USDC SUPPLY ANALYSIS")
        print("="*60)
        
        results = {}
        
        # Basic statistics
        results['total_events'] = len(self.df)
        results['total_usdc_supplied'] = self.df['amount_usdc'].sum()
        results['unique_suppliers'] = self.df['on_behalf_of'].nunique()
        results['unique_users'] = self.df['user'].nunique()
        results['avg_supply_per_tx'] = self.df['amount_usdc'].mean()
        results['median_supply_per_tx'] = self.df['amount_usdc'].median()
        results['min_supply'] = self.df['amount_usdc'].min()
        results['max_supply'] = self.df['amount_usdc'].max()
        
        # Whale analysis (top suppliers by cumulative amount)
        whale_data = self._analyze_whales()
        results['top_whale_address'] = whale_data['address']
        results['top_whale_total_usdc'] = whale_data['total_usdc']
        results['top_whale_tx_count'] = whale_data['tx_count']
        results['top_whale_percentage'] = whale_data['percentage']
        
        # Distribution analysis
        results['top_10_suppliers_percentage'] = self._top_n_percentage(10)
        results['top_50_suppliers_percentage'] = self._top_n_percentage(50)
        
        # Transaction size categories
        size_dist = self._analyze_transaction_sizes()
        results['small_tx_count'] = size_dist['small']
        results['medium_tx_count'] = size_dist['medium']
        results['large_tx_count'] = size_dist['large']
        results['whale_tx_count'] = size_dist['whale']
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _analyze_whales(self) -> Dict:
        """
        Identify and analyze whale suppliers
        
        Returns:
            Dictionary with whale information
        """
        # Group by on_behalf_of and sum amounts
        supplier_totals = self.df.groupby('on_behalf_of').agg({
            'amount_usdc': ['sum', 'count']
        }).reset_index()
        
        supplier_totals.columns = ['address', 'total_usdc', 'tx_count']
        supplier_totals = supplier_totals.sort_values('total_usdc', ascending=False)
        
        # Get top whale
        top_whale = supplier_totals.iloc[0]
        total_supply = self.df['amount_usdc'].sum()
        
        return {
            'address': top_whale['address'],
            'total_usdc': top_whale['total_usdc'],
            'tx_count': int(top_whale['tx_count']),
            'percentage': (top_whale['total_usdc'] / total_supply) * 100,
            'all_whales': supplier_totals
        }
    
    def _top_n_percentage(self, n: int) -> float:
        """
        Calculate what percentage of total supply comes from top N suppliers
        
        Args:
            n: Number of top suppliers
            
        Returns:
            Percentage of total supply
        """
        supplier_totals = self.df.groupby('on_behalf_of')['amount_usdc'].sum()
        top_n_supply = supplier_totals.nlargest(n).sum()
        total_supply = self.df['amount_usdc'].sum()
        
        return (top_n_supply / total_supply) * 100
    
    def _analyze_transaction_sizes(self) -> Dict:
        """
        Categorize transactions by size
        
        Returns:
            Dictionary with counts for each category
        """
        # Define categories (in USDC)
        small_threshold = 1000
        medium_threshold = 10000
        large_threshold = 100000
        
        return {
            'small': len(self.df[self.df['amount_usdc'] < small_threshold]),
            'medium': len(self.df[
                (self.df['amount_usdc'] >= small_threshold) & 
                (self.df['amount_usdc'] < medium_threshold)
            ]),
            'large': len(self.df[
                (self.df['amount_usdc'] >= medium_threshold) & 
                (self.df['amount_usdc'] < large_threshold)
            ]),
            'whale': len(self.df[self.df['amount_usdc'] >= large_threshold])
        }
    
    def _print_summary(self, results: Dict):
        """Print formatted analysis summary"""
        print(f"\n📊 OVERVIEW")
        print(f"   Total Events: {results['total_events']:,}")
        print(f"   Total USDC Supplied: ${results['total_usdc_supplied']:,.2f}")
        print(f"   Unique Suppliers (onBehalfOf): {results['unique_suppliers']:,}")
        print(f"   Unique Users: {results['unique_users']:,}")
        
        print(f"\n📈 TRANSACTION STATISTICS")
        print(f"   Average Supply per TX: ${results['avg_supply_per_tx']:,.2f}")
        print(f"   Median Supply per TX: ${results['median_supply_per_tx']:,.2f}")
        print(f"   Min Supply: ${results['min_supply']:,.2f}")
        print(f"   Max Supply: ${results['max_supply']:,.2f}")
        
        print(f"\n🐋 WHALE ANALYSIS")
        print(f"   Top Whale Address: {results['top_whale_address']}")
        print(f"   Top Whale Total: ${results['top_whale_total_usdc']:,.2f}")
        print(f"   Top Whale TX Count: {results['top_whale_tx_count']}")
        print(f"   Top Whale % of Total: {results['top_whale_percentage']:.2f}%")
        
        print(f"\n📊 CONCENTRATION")
        print(f"   Top 10 Suppliers: {results['top_10_suppliers_percentage']:.2f}% of total")
        print(f"   Top 50 Suppliers: {results['top_50_suppliers_percentage']:.2f}% of total")
        
        print(f"\n💰 TRANSACTION SIZE DISTRIBUTION")
        print(f"   Small (<$1K): {results['small_tx_count']} transactions")
        print(f"   Medium ($1K-$10K): {results['medium_tx_count']} transactions")
        print(f"   Large ($10K-$100K): {results['large_tx_count']} transactions")
        print(f"   Whale (>$100K): {results['whale_tx_count']} transactions")
        print("="*60)
    
    def save_to_csv(self):
        """Save raw data and summary to CSV files"""
        print(f"\n💾 Saving results to CSV files...")
        
        # Save raw event data
        self.df.to_csv(OUTPUT_CSV, index=False)
        print(f"   ✓ Raw data saved to: {OUTPUT_CSV}")
        
        # Create and save summary
        whale_data = self._analyze_whales()
        top_suppliers = whale_data['all_whales'].head(50)
        top_suppliers.to_csv(SUMMARY_CSV, index=False)
        print(f"   ✓ Top suppliers saved to: {SUMMARY_CSV}")
        
        return OUTPUT_CSV, SUMMARY_CSV
    
    def get_top_suppliers(self, n: int = 10) -> pd.DataFrame:
        """
        Get top N suppliers by total USDC supplied
        
        Args:
            n: Number of top suppliers to return
            
        Returns:
            DataFrame with top suppliers
        """
        whale_data = self._analyze_whales()
        return whale_data['all_whales'].head(n)
    
    def generate_detailed_report(self) -> str:
        """
        Generate a detailed text report
        
        Returns:
            Formatted report string
        """
        results = self.analyze()
        
        report = []
        report.append("="*60)
        report.append("AAVE V3 USDC SUPPLY DETAILED REPORT")
        report.append("="*60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Add all analysis sections
        report.append("OVERVIEW:")
        report.append(f"  Total Events Analyzed: {results['total_events']:,}")
        report.append(f"  Total USDC Supplied: ${results['total_usdc_supplied']:,.2f}")
        report.append(f"  Unique Suppliers: {results['unique_suppliers']:,}")
        report.append("")
        
        report.append("TOP 10 SUPPLIERS:")
        top_10 = self.get_top_suppliers(10)
        for idx, row in top_10.iterrows():
            report.append(f"  {idx+1}. {row['address']}: ${row['total_usdc']:,.2f} ({int(row['tx_count'])} txs)")
        
        return "\n".join(report)