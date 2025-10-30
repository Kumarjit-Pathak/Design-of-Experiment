"""
E-commerce Customer Data Generator

This script generates a realistic dataset of 20,000 e-commerce customers
with diverse characteristics for demonstrating Design of Experiments techniques.

The dataset includes:
- Customer demographics (age, gender, location, income, education)
- Shopping behavior (orders, order value, category preferences)
- Engagement metrics (email open rate, website visits, app usage)
- Behavioral indicators (cart abandonment, reviews, ratings)
- Target variables (conversion, lifetime value, churn, marketing response)

Author: DOE Simulator Team
Date: 2025
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class EcommerceDataGenerator:
    """
    Generate realistic e-commerce customer data with correlated features.

    This class creates synthetic data that mimics real-world patterns:
    - Income correlates with order value
    - Younger users prefer mobile apps
    - Loyalty members have higher engagement
    - Recent activity predicts conversion
    """

    def __init__(self, n_samples=20000, random_seed=42):
        """
        Initialize the data generator.

        Args:
            n_samples: Number of customer records to generate (default: 20,000)
            random_seed: Random seed for reproducibility (default: 42)
        """
        self.n_samples = n_samples
        self.random_seed = random_seed
        np.random.seed(random_seed)

    def generate_demographics(self):
        """
        Generate customer demographic features.

        Returns:
            dict: Dictionary containing demographic features
        """
        # Age: Normal distribution centered at 38, range 18-75
        age = np.clip(np.random.normal(38, 12, self.n_samples), 18, 75).astype(int)

        # Gender: Balanced distribution with some non-binary representation
        gender = np.random.choice(
            ['Male', 'Female', 'Non-binary'],
            size=self.n_samples,
            p=[0.48, 0.49, 0.03]
        )

        # Location: Skewed towards urban areas
        location = np.random.choice(
            ['Urban', 'Suburban', 'Rural'],
            size=self.n_samples,
            p=[0.45, 0.40, 0.15]
        )

        # Income Level: Influenced by age (peaks in mid-career)
        # Create age-based income probability
        income_base = np.random.rand(self.n_samples)
        age_factor = np.clip((age - 20) / 30, 0, 1)  # Income increases with age up to 50
        income_adjusted = income_base * 0.6 + age_factor * 0.4

        income_level = pd.cut(
            income_adjusted,
            bins=[0, 0.25, 0.60, 0.85, 1.0],
            labels=['Low', 'Medium', 'High', 'Very High']
        ).astype(str)

        # Education: Correlated with income
        education_probs = {
            'Low': [0.40, 0.35, 0.20, 0.05],
            'Medium': [0.25, 0.40, 0.25, 0.10],
            'High': [0.15, 0.30, 0.35, 0.20],
            'Very High': [0.10, 0.25, 0.35, 0.30]
        }

        education = []
        for inc in income_level:
            edu = np.random.choice(
                ['High School', 'Bachelor', 'Master', 'PhD'],
                p=education_probs[inc]
            )
            education.append(edu)

        return {
            'age': age,
            'gender': gender,
            'location': location,
            'income_level': income_level,
            'education': education
        }

    def generate_shopping_behavior(self, demographics):
        """
        Generate shopping behavior features correlated with demographics.

        Args:
            demographics: Dict of demographic features

        Returns:
            dict: Dictionary containing shopping behavior features
        """
        # Account age: Longer for older customers
        age_factor = (demographics['age'] - 18) / 57  # Normalize to 0-1
        account_age_days = np.random.exponential(
            scale=500 * (1 + age_factor),
            size=self.n_samples
        ).clip(0, 3650).astype(int)

        # Total orders: Influenced by account age and income
        income_multiplier = {
            'Low': 0.7, 'Medium': 1.0, 'High': 1.3, 'Very High': 1.6
        }
        income_mult = np.array([income_multiplier[inc] for inc in demographics['income_level']])

        total_orders = np.random.poisson(
            lam=(account_age_days / 100) * income_mult
        ).clip(0, 200)

        # Average order value: Strongly correlated with income
        base_order_value = {
            'Low': (30, 20), 'Medium': (60, 30),
            'High': (120, 50), 'Very High': (200, 80)
        }

        avg_order_value = []
        for inc in demographics['income_level']:
            mean, std = base_order_value[inc]
            value = np.random.normal(mean, std)
            avg_order_value.append(max(10, value))

        avg_order_value = np.array(avg_order_value).round(2)

        # Last order days ago: Exponential distribution
        last_order_days_ago = np.random.exponential(
            scale=60, size=self.n_samples
        ).clip(0, 365).astype(int)

        # Product category preference: Varies by age and gender
        categories = ['Electronics', 'Fashion', 'Home', 'Books', 'Sports']
        product_category_preference = []

        for a, g in zip(demographics['age'], demographics['gender']):
            if a < 30:
                # Younger: Electronics, Fashion
                probs = [0.35, 0.35, 0.10, 0.10, 0.10]
            elif a < 50:
                # Middle-aged: Home, Fashion
                probs = [0.20, 0.25, 0.30, 0.15, 0.10]
            else:
                # Older: Books, Home
                probs = [0.15, 0.15, 0.30, 0.25, 0.15]

            category = np.random.choice(categories, p=probs)
            product_category_preference.append(category)

        return {
            'account_age_days': account_age_days,
            'total_orders': total_orders,
            'avg_order_value': avg_order_value,
            'last_order_days_ago': last_order_days_ago,
            'product_category_preference': product_category_preference
        }

    def generate_engagement_metrics(self, demographics, shopping):
        """
        Generate engagement metrics correlated with other features.

        Args:
            demographics: Dict of demographic features
            shopping: Dict of shopping behavior features

        Returns:
            dict: Dictionary containing engagement metrics
        """
        # Email open rate: Higher for active customers
        activity_score = (shopping['total_orders'] / 50).clip(0, 1)
        email_open_rate = np.random.beta(
            a=2 + 3 * activity_score,
            b=5 - 2 * activity_score
        ) * 100
        email_open_rate = email_open_rate.clip(0, 100).round(1)

        # Website visits per month: Younger and urban customers visit more
        age_factor = 1 - (demographics['age'] - 18) / 57
        location_factor = {
            'Urban': 1.3, 'Suburban': 1.0, 'Rural': 0.7
        }
        loc_mult = np.array([location_factor[loc] for loc in demographics['location']])

        website_visits = np.random.poisson(
            lam=15 * age_factor * loc_mult
        ).clip(0, 50)

        # Mobile app user: Younger customers more likely
        mobile_prob = 0.8 - (demographics['age'] - 18) / 100
        mobile_app_user = np.random.rand(self.n_samples) < mobile_prob
        mobile_app_user = ['Yes' if x else 'No' for x in mobile_app_user]

        # Loyalty program member: Active shoppers more likely
        loyalty_prob = (shopping['total_orders'] / 100).clip(0, 0.85)
        loyalty_program_member = np.random.rand(self.n_samples) < loyalty_prob
        loyalty_program_member = ['Yes' if x else 'No' for x in loyalty_program_member]

        # Customer service interactions: More for issues/active users
        cs_interactions = np.random.poisson(
            lam=shopping['total_orders'] * 0.05
        ).clip(0, 20)

        return {
            'email_open_rate': email_open_rate,
            'website_visits_per_month': website_visits,
            'mobile_app_user': mobile_app_user,
            'loyalty_program_member': loyalty_program_member,
            'customer_service_interactions': cs_interactions
        }

    def generate_behavioral_indicators(self, engagement, shopping):
        """
        Generate behavioral indicators.

        Args:
            engagement: Dict of engagement metrics
            shopping: Dict of shopping behavior features

        Returns:
            dict: Dictionary containing behavioral indicators
        """
        # Cart abandonment rate: Inversely related to conversion
        # Higher for less engaged customers
        engagement_score = (engagement['email_open_rate'] / 100)
        cart_abandonment = (1 - engagement_score) * np.random.uniform(40, 80, self.n_samples)
        cart_abandonment_rate = cart_abandonment.clip(0, 100).round(1)

        # Review count: Proportional to orders
        review_count = np.random.binomial(
            n=shopping['total_orders'],
            p=0.15
        ).clip(0, 100)

        # Average rating given: Most customers give 4-5 stars
        avg_rating_given = np.random.beta(a=8, b=2, size=self.n_samples) * 4 + 1
        avg_rating_given = avg_rating_given.clip(1, 5).round(1)

        # Social media follower: More likely for engaged customers
        social_prob = engagement_score * 0.6 + 0.1
        social_media_follower = np.random.rand(self.n_samples) < social_prob
        social_media_follower = ['Yes' if x else 'No' for x in social_media_follower]

        return {
            'cart_abandonment_rate': cart_abandonment_rate,
            'review_count': review_count,
            'avg_rating_given': avg_rating_given,
            'social_media_follower': social_media_follower
        }

    def generate_target_variables(self, demographics, shopping, engagement, behavioral):
        """
        Generate target variables for experiments.

        Args:
            demographics: Dict of demographic features
            shopping: Dict of shopping behavior features
            engagement: Dict of engagement metrics
            behavioral: Dict of behavioral indicators

        Returns:
            dict: Dictionary containing target variables
        """
        # Conversion rate: Complex function of multiple factors
        age_factor = 1 - abs(demographics['age'] - 40) / 40  # Peak at age 40
        income_factor = {
            'Low': 0.7, 'Medium': 0.9, 'High': 1.1, 'Very High': 1.2
        }
        inc_mult = np.array([income_factor[inc] for inc in demographics['income_level']])

        engagement_score = engagement['email_open_rate'] / 100
        loyalty_boost = np.array([1.3 if x == 'Yes' else 1.0
                                 for x in engagement['loyalty_program_member']])

        conversion_base = age_factor * inc_mult * engagement_score * loyalty_boost
        conversion_rate = (conversion_base * 60 + np.random.normal(0, 10, self.n_samples))
        conversion_rate = conversion_rate.clip(0, 100).round(1)

        # Lifetime value: Based on orders and order value
        lifetime_value = (
            shopping['total_orders'] * shopping['avg_order_value'] *
            (1 + engagement_score * 0.3)
        )
        lifetime_value = lifetime_value.clip(0, 10000).round(2)

        # Churn probability: Higher for inactive customers
        recency_factor = shopping['last_order_days_ago'] / 365
        churn_probability = (
            recency_factor * 60 +
            (1 - engagement_score) * 30 +
            behavioral['cart_abandonment_rate'] * 0.2 +
            np.random.normal(0, 10, self.n_samples)
        )
        churn_probability = churn_probability.clip(0, 100).round(1)

        # Response to marketing: Binary based on engagement
        marketing_score = (
            engagement_score * 0.4 +
            (shopping['total_orders'] / 100).clip(0, 1) * 0.3 +
            (1 - recency_factor) * 0.3
        )
        response_to_marketing = (np.random.rand(self.n_samples) < marketing_score).astype(int)

        return {
            'conversion_rate': conversion_rate,
            'lifetime_value': lifetime_value,
            'churn_probability': churn_probability,
            'response_to_marketing': response_to_marketing
        }

    def introduce_missing_data(self, df, missing_rate=0.05):
        """
        Introduce realistic missing data patterns.

        Args:
            df: DataFrame with complete data
            missing_rate: Proportion of missing data (default: 5%)

        Returns:
            DataFrame with missing values
        """
        # Columns that can have missing data (not IDs or critical features)
        missable_columns = [
            'email_open_rate', 'avg_rating_given', 'customer_service_interactions',
            'review_count', 'cart_abandonment_rate'
        ]

        for col in missable_columns:
            if col in df.columns:
                missing_mask = np.random.rand(len(df)) < missing_rate
                df.loc[missing_mask, col] = np.nan

        return df

    def generate(self, include_missing=True):
        """
        Generate the complete dataset.

        Args:
            include_missing: Whether to introduce missing data (default: True)

        Returns:
            pandas.DataFrame: Complete generated dataset
        """
        print(f"Generating {self.n_samples:,} customer records...")

        # Generate feature groups
        demographics = self.generate_demographics()
        print("[OK] Demographics generated")

        shopping = self.generate_shopping_behavior(demographics)
        print("[OK] Shopping behavior generated")

        engagement = self.generate_engagement_metrics(demographics, shopping)
        print("[OK] Engagement metrics generated")

        behavioral = self.generate_behavioral_indicators(engagement, shopping)
        print("[OK] Behavioral indicators generated")

        targets = self.generate_target_variables(
            demographics, shopping, engagement, behavioral
        )
        print("[OK] Target variables generated")

        # Combine all features
        data = {
            'customer_id': [f'CUST{i:06d}' for i in range(1, self.n_samples + 1)],
            **demographics,
            **shopping,
            **engagement,
            **behavioral,
            **targets
        }

        df = pd.DataFrame(data)

        # Introduce missing data if requested
        if include_missing:
            df = self.introduce_missing_data(df)
            print("[OK] Missing data introduced (5%)")

        print(f"\n[SUCCESS] Dataset generation complete!")
        print(f"   Shape: {df.shape}")
        print(f"   Features: {len(df.columns)}")

        return df


def main():
    """Main function to generate and save the dataset."""
    # Generate dataset
    generator = EcommerceDataGenerator(n_samples=20000, random_seed=42)
    df = generator.generate(include_missing=True)

    # Save to CSV
    output_path = 'data/raw/ecommerce_data.csv'
    df.to_csv(output_path, index=False)
    print(f"\n[SAVED] Dataset saved to: {output_path}")

    # Display summary statistics
    print("\n" + "="*70)
    print("DATASET SUMMARY")
    print("="*70)

    print(f"\nShape: {df.shape[0]:,} rows x {df.shape[1]} columns")

    print("\nFeature Categories:")
    demographics_cols = ['age', 'gender', 'location', 'income_level', 'education']
    shopping_cols = ['account_age_days', 'total_orders', 'avg_order_value',
                     'last_order_days_ago', 'product_category_preference']
    engagement_cols = ['email_open_rate', 'website_visits_per_month',
                      'mobile_app_user', 'loyalty_program_member',
                      'customer_service_interactions']
    behavioral_cols = ['cart_abandonment_rate', 'review_count',
                      'avg_rating_given', 'social_media_follower']
    target_cols = ['conversion_rate', 'lifetime_value', 'churn_probability',
                   'response_to_marketing']

    print(f"  - Demographics: {len(demographics_cols)}")
    print(f"  - Shopping Behavior: {len(shopping_cols)}")
    print(f"  - Engagement Metrics: {len(engagement_cols)}")
    print(f"  - Behavioral Indicators: {len(behavioral_cols)}")
    print(f"  - Target Variables: {len(target_cols)}")

    print("\nSample Statistics:")
    print(f"  - Average Age: {df['age'].mean():.1f} years")
    print(f"  - Average Total Orders: {df['total_orders'].mean():.1f}")
    print(f"  - Average Order Value: ${df['avg_order_value'].mean():.2f}")
    print(f"  - Average Lifetime Value: ${df['lifetime_value'].mean():.2f}")
    print(f"  - Marketing Response Rate: {df['response_to_marketing'].mean()*100:.1f}%")

    print("\nMissing Data:")
    missing_counts = df.isnull().sum()
    missing_cols = missing_counts[missing_counts > 0]
    if len(missing_cols) > 0:
        for col, count in missing_cols.items():
            print(f"  - {col}: {count} ({count/len(df)*100:.1f}%)")
    else:
        print("  - No missing data")

    print("\n" + "="*70)

    # Display first few rows
    print("\nFirst 5 rows:")
    print(df.head().to_string())

    print("\n[SUCCESS] Phase 1 Complete: Data Generation Successful!")


if __name__ == "__main__":
    main()
