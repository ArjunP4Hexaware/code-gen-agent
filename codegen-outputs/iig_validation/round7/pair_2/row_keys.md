# Row keys - scrubbed export

Every value below is scrubbed: a scrub_check class (and a local-denylist term) is `<CLASS>`; a token found in the golden but not in the repo's committed fixtures is `G<n>`, any other token outside the fixtures is `A<n>` - one map for every file of this export, so the same token is the same placeholder everywhere. Tokens under 3 characters and numbers under 5 digits are kept. CREATED_BY / UPDATED_BY values are withheld.

## EMAIL_TEMPLATE_CONFIG

- presence: compared; pair mode: key
- key columns used for pairing: TEMPLATE_NAME, STATUS
- rows: golden 12, agent 6, paired 0

### Golden rows

| golden row | key | status | agent row | source exports |
| --- | --- | --- | --- | --- |
| 2 | G1 G2 \| Success | unpaired | - | 1: G28 |
| 3 | G1 G2 \| Success | unpaired | - | 1: G29 |
| 4 | G1 G2 \| Success | unpaired | - | 1: G30 |
| 5 | G1 G2 \| Success | unpaired | - | 1: G31 |
| 6 | G1 G2 \| Success | unpaired | - | 1: G32 |
| 7 | G1 G2 \| Success | unpaired | - | 1: G33 |
| 8 | G1 G2 \| Failed | unpaired | - | 1: G28 |
| 9 | G1 G2 \| Failed | unpaired | - | 1: G29 |
| 10 | G1 G2 \| Failed | unpaired | - | 1: G30 |
| 11 | G1 G2 \| Failed | unpaired | - | 1: G31 |
| 12 | G1 G2 \| Failed | unpaired | - | 1: G32 |
| 13 | G1 G2 \| Failed | unpaired | - | 1: G33 |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 1:2 | <blank> \| Success | unpaired | - |
| 1:3 | <blank> \| Failed | unpaired | - |
| 2:2 | <blank> \| Success | unpaired | - |
| 2:3 | <blank> \| Failed | unpaired | - |
| 3:2 | <blank> \| Success | unpaired | - |
| 3:3 | <blank> \| Failed | unpaired | - |

## adls_delta_ingestion_details

- presence: compared; pair mode: key
- key columns used for pairing: OBJECT_NAME, TGT_TABLE_NAME
- rows: golden 3, agent 3, paired 3

### Golden rows

| golden row | key | status | agent row | source exports |
| --- | --- | --- | --- | --- |
| 2 | demographics_package \| sd_community_demographic_risk | paired | 1:2 | 1: G28 |
| 3 | analytics_package \| sd_community_risk | paired | 2:2 | 1: G30 |
| 4 | sd_ind_risk_data_package_G23_MI \| sd_individual_risk | paired | 3:2 | 1: G32 |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 1:2 | demographics_package \| sd_community_demographic_risk | paired | 2 |
| 2:2 | analytics_package \| sd_community_risk | paired | 3 |
| 3:2 | sd_ind_risk_data_package_G23_MI \| sd_individual_risk | paired | 4 |

## all_files_static_information

- presence: compared; pair mode: key
- key columns used for pairing: FILE_NAME
- rows: golden 3, agent 3, paired 0

### Golden rows

| golden row | key | status | agent row | source exports |
| --- | --- | --- | --- | --- |
| 2 | demographics_package | unpaired | - | 6: G28,G29,G30,G31,G32,G33 |
| 3 | analytics_package | unpaired | - | 6: G28,G29,G30,G31,G32,G33 |
| 4 | sd_ind_risk_data_package_G23_MI | unpaired | - | 6: G28,G29,G30,G31,G32,G33 |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 1:2 | (key column absent) | unpaired | - |
| 2:2 | (key column absent) | unpaired | - |
| 3:2 | (key column absent) | unpaired | - |

## data_factory_pipeline_schedule

- presence: compared; pair mode: key
- key columns used for pairing: PIPELINE_NAME
- rows: golden 6, agent 12, paired 0

### Golden rows

| golden row | key | status | agent row | source exports |
| --- | --- | --- | --- | --- |
| 2 | PL_File_G2_G3_G4_ADLS_To_Delta_Incr | unpaired | - | 6: G28,G29,G30,G31,G32,G33 |
| 3 | PL_File_G2_G3_G4_Delta_To_STD_Incr | unpaired | - | 6: G28,G29,G30,G31,G32,G33 |
| 4 | PL_File_G2_G21_G4_ADLS_To_Delta_Incr | unpaired | - | 6: G28,G29,G30,G31,G32,G33 |
| 5 | PL_File_G2_G21_G4_Delta_To_STD_Incr | unpaired | - | 6: G28,G29,G30,G31,G32,G33 |
| 6 | PL_File_G2_SD_IND_RISK_ADLS_To_Delta_Incr | unpaired | - | 6: G28,G29,G30,G31,G32,G33 |
| 7 | PL_File_G2_SD_IND_RISK_Delta_To_STD_Incr | unpaired | - | 6: G28,G29,G30,G31,G32,G33 |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 1:2 | PL_GMSTR_SD_COMMUNITY_DEMOGRAPHIC_RISK | unpaired | - |
| 1:3 | PL_MSTR_SD_COMMUNITY_DEMOGRAPHIC_RISK | unpaired | - |
| 1:4 | PL_File_SD_COMMUNITY_DEMOGRAPHIC_RISK_ADLS_To_Delta_Incr | unpaired | - |
| 1:5 | PL_File_SD_COMMUNITY_DEMOGRAPHIC_RISK_Delta_To_STD_Incr | unpaired | - |
| 2:2 | PL_GMSTR_SD_COMMUNITY_RISK | unpaired | - |
| 2:3 | PL_MSTR_SD_COMMUNITY_RISK | unpaired | - |
| 2:4 | PL_File_SD_COMMUNITY_RISK_ADLS_To_Delta_Incr | unpaired | - |
| 2:5 | PL_File_SD_COMMUNITY_RISK_Delta_To_STD_Incr | unpaired | - |
| 3:2 | PL_GMSTR_SD_INDIVIDUAL_RISK | unpaired | - |
| 3:3 | PL_MSTR_SD_INDIVIDUAL_RISK | unpaired | - |
| 3:4 | PL_File_SD_INDIVIDUAL_RISK_ADLS_To_Delta_Incr | unpaired | - |
| 3:5 | PL_File_SD_INDIVIDUAL_RISK_Delta_To_STD_Incr | unpaired | - |

## data_quality_rules

- presence: compared; pair mode: key
- key columns used for pairing: OBJECT_ID -> table, RULE_CLASS, SOURCE_COLUMN
- rows: golden 10, agent 0, paired 0

### Golden rows

| golden row | key | status | agent row | source exports |
| --- | --- | --- | --- | --- |
| 2 | sd_community_demographic_risk \| G27 \| zip_code | unpaired | - | 2: G28,G30 |
| 3 | sd_community_demographic_risk \| LRTrimRule \| gender_female_pct,gender_male_pct,race_white_pct,race_black_pct,race_asian_pct,race_other_alone_pct,race_two_or_more_pct,ethnicity_hispanic_pct,ethnicity_hispanic_white_pct,ethnicity_hispanic_other_pct,age_female_0_17_pct,age_female_18_24_pct,age_female_25_34_pct,age_female_35_44_pct,age_female_45_54_pct,age_female_55_64_pct,age_female_65_74_pct,age_female_75_84_pct,age_female_85_over_pct,age_male_0_17_pct,age_male_18_24_pct,age_male_25_34_pct,age_male_35_44_pct,age_male_45_54_pct,age_male_55_64_pct,age_male_65_74_pct,age_male_75_84_pct,age_male_85_over_pct,language_english_pct,language_spanish_pct,language_other_european_pct,language_asian_pct,language_other_pct,veteran_pct,veteran_male_pct,education_no_hs_pct,education_hs_ged_pct,education_some_college_pct,education_college_degree_pct,education_adv_degree_pct | unpaired | - | 1: G29 |
| 4 | sd_community_demographic_risk \| DataTypeCastRule \| gender_female_pct,gender_male_pct,race_white_pct,race_black_pct,race_asian_pct,race_other_alone_pct,race_two_or_more_pct,ethnicity_hispanic_pct,ethnicity_hispanic_white_pct,ethnicity_hispanic_other_pct,age_female_0_17_pct,age_female_18_24_pct,age_female_25_34_pct,age_female_35_44_pct,age_female_45_54_pct,age_female_55_64_pct,age_female_65_74_pct,age_female_75_84_pct,age_female_85_over_pct,age_male_0_17_pct,age_male_18_24_pct,age_male_25_34_pct,age_male_35_44_pct,age_male_45_54_pct,age_male_55_64_pct,age_male_65_74_pct,age_male_75_84_pct,age_male_85_over_pct,language_english_pct,language_spanish_pct,language_other_european_pct,language_asian_pct,language_other_pct,veteran_pct,veteran_male_pct,education_no_hs_pct,education_hs_ged_pct,education_some_college_pct,education_college_degree_pct,education_adv_degree_pct | unpaired | - | 1: G29 |
| 5 | sd_community_risk \| LRTrimRule \| economic_risk_score,economic_risk_score_2_hex_pct,economic_risk_score_3_hex_pct,economic_risk_score_2_population_pct,economic_risk_score_3_population_pct,pct_of_population_under_fpl,opportunity_index,food_risk_score,food_risk_score_1_hex_pct,food_risk_score_2_hex_pct,food_risk_score_3_hex_pct,food_risk_score_1_population_pct,food_risk_score_2_population_pct,food_risk_score_3_population_pct,food_illiteracy_rate,estimated_snap_eligible_households,snap_utilizing_households,healthy_food_balance,healthy_food_options_per_10k,unhealthy_food_options_per_10k,full_service_groceries_per_10k,fast_food_per_10k,housing_risk_score_1_hex_pct,housing_risk_score_2_hex_pct,housing_risk_score_3_hex_pct,housing_risk_score_1_population_pct,housing_risk_score_2_population_pct,housing_risk_score_3_population_pct,median_housing_cost_as_pct_of_income,bedrooms_per_person,rooms_per_person,median_household_size,old_households,crowded_households,median_household_mold_index,rented_households,owned_households,median_gross_rent_as_pct_of_income,households_lacking_kitchens,housing_condition_index,transportation_risk_score,transportation_risk_score_1_hex_pct,transportation_risk_score_2_hex_pct,transportation_risk_score_3_hex_pct,transportation_risk_score_1_population_pct,transportation_risk_score_2_population_pct,transportation_risk_score_3_population_pct,median_vehicles_per_household,providers_per_10k,health_literacy_risk_score_1_hex_pct,health_literacy_risk_score_2_hex_pct,health_literacy_risk_score_3_hex_pct,health_literacy_risk_score_1_population_pct,health_literacy_risk_score_2_population_pct,health_literacy_risk_score_3_population_pct,population_without_health_insurance,educational_attainment_index,education_no_hs_pct,education_hs_ged_pct,education_some_college_pct,education_college_degree_pct,education_adv_degree_pct,health_environment_index,language_english_pct,language_spanish_pct,language_other_pct,digital_landscape_risk_score_2_hex_pct,digital_landscape_risk_score_3_hex_pct,digital_landscape_risk_score_4_hex_pct,digital_landscape_risk_score_2_population_pct,digital_landscape_risk_score_3_population_pct,digital_landscape_risk_score_4_population_pct,digital_landscape_elevated_risk_population_pct,digital_landscape_elevated_risk_hex_pct,population_not_utilizing_broadband_pct,library_quality_index,social_connectedness_risk_score,social_connectedness_risk_score_2_hex_pct,social_connectedness_risk_score_3_hex_pct,social_connectedness_risk_score_4_hex_pct,social_connectedness_risk_score_2_population_pct,social_connectedness_risk_score_3_population_pct,social_connectedness_risk_score_4_population_pct,social_connectedness_elevated_risk_population_pct,social_connectedness_elevated_risk_hex_pct,social_detachment_index,social_interactions_index,social_network_density_index,social_support_locations_per_10k,mental_health_barriers_index | unpaired | - | 1: G31 |
| 6 | sd_community_risk \| DataTypeCastRule \| economic_risk_score,economic_risk_score_2_hex_pct,economic_risk_score_3_hex_pct,economic_risk_score_2_population_pct,economic_risk_score_3_population_pct,pct_of_population_under_fpl,opportunity_index,food_risk_score,food_risk_score_1_hex_pct,food_risk_score_2_hex_pct,food_risk_score_3_hex_pct,food_risk_score_1_population_pct,food_risk_score_2_population_pct,food_risk_score_3_population_pct,food_illiteracy_rate,estimated_snap_eligible_households,snap_utilizing_households,healthy_food_balance,healthy_food_options_per_10k,unhealthy_food_options_per_10k,full_service_groceries_per_10k,fast_food_per_10k,housing_risk_score_1_hex_pct,housing_risk_score_2_hex_pct,housing_risk_score_3_hex_pct,housing_risk_score_1_population_pct,housing_risk_score_2_population_pct,housing_risk_score_3_population_pct,median_housing_cost_as_pct_of_income,bedrooms_per_person,rooms_per_person,median_household_size,old_households,crowded_households,median_household_mold_index,rented_households,owned_households,median_gross_rent_as_pct_of_income,households_lacking_kitchens,housing_condition_index,transportation_risk_score,transportation_risk_score_1_hex_pct,transportation_risk_score_2_hex_pct,transportation_risk_score_3_hex_pct,transportation_risk_score_1_population_pct,transportation_risk_score_2_population_pct,transportation_risk_score_3_population_pct,median_vehicles_per_household,providers_per_10k,health_literacy_risk_score_1_hex_pct,health_literacy_risk_score_2_hex_pct,health_literacy_risk_score_3_hex_pct,health_literacy_risk_score_1_population_pct,health_literacy_risk_score_2_population_pct,health_literacy_risk_score_3_population_pct,population_without_health_insurance,educational_attainment_index,education_no_hs_pct,education_hs_ged_pct,education_some_college_pct,education_college_degree_pct,education_adv_degree_pct,health_environment_index,language_english_pct,language_spanish_pct,language_other_pct,digital_landscape_risk_score_2_hex_pct,digital_landscape_risk_score_3_hex_pct,digital_landscape_risk_score_4_hex_pct,digital_landscape_risk_score_2_population_pct,digital_landscape_risk_score_3_population_pct,digital_landscape_risk_score_4_population_pct,digital_landscape_elevated_risk_population_pct,digital_landscape_elevated_risk_hex_pct,population_not_utilizing_broadband_pct,library_quality_index,social_connectedness_risk_score,social_connectedness_risk_score_2_hex_pct,social_connectedness_risk_score_3_hex_pct,social_connectedness_risk_score_4_hex_pct,social_connectedness_risk_score_2_population_pct,social_connectedness_risk_score_3_population_pct,social_connectedness_risk_score_4_population_pct,social_connectedness_elevated_risk_population_pct,social_connectedness_elevated_risk_hex_pct,social_detachment_index,social_interactions_index,social_network_density_index,social_support_locations_per_10k,mental_health_barriers_index | unpaired | - | 1: G31 |
| 7 | sd_individual_risk \| G27 \| member_id | unpaired | - | 1: G32 |
| 8 | sd_individual_risk \| ReferentialCheckRule \| member_id | unpaired | - | 1: G32 |
| 9 | sd_individual_risk \| LRTrimRule \| sd_ind_financial_strain,sd_household_gipah,sd_opportunity_index,sd_ind_food_insecurity,sd_ind_healthy_food_balance,sd_ind_food_swamp_indicator,sd_ind_food_desert_indicator,sd_ind_housing_instability,sd_address_volatility,sd_crowding_index,sd_housing_quality_index,sd_ind_household_size,sd_occupancy_score,sd_ind_transportation_barriers,sd_ind_public_transportation_index,sd_ind_health_resources_index,sd_provider_desert_indicator,sd_pharmacy_desert_indicator,sd_hospital_desert_indicator,sd_pcp_desert_indicator,sd_high_volume_specialists_desert_indicator,sd_high_impact_specialists_desert_indicator,sd_behavioral_health_specialists_desert_indicator,sd_car_ownership,sd_ind_health_literacy_challenges,sd_language_other_than_english,sd_lack_of_education,sd_date_scored | unpaired | - | 1: G33 |
| 10 | sd_individual_risk \| DataTypeCastRule \| sd_ind_financial_strain,sd_household_gipah,sd_opportunity_index,sd_ind_food_insecurity,sd_ind_healthy_food_balance,sd_ind_food_swamp_indicator,sd_ind_food_desert_indicator,sd_ind_housing_instability,sd_address_volatility,sd_crowding_index,sd_housing_quality_index,sd_ind_household_size,sd_occupancy_score,sd_ind_transportation_barriers,sd_ind_public_transportation_index,sd_ind_health_resources_index,sd_provider_desert_indicator,sd_pharmacy_desert_indicator,sd_hospital_desert_indicator,sd_pcp_desert_indicator,sd_high_volume_specialists_desert_indicator,sd_high_impact_specialists_desert_indicator,sd_behavioral_health_specialists_desert_indicator,sd_car_ownership,sd_ind_health_literacy_challenges,sd_language_other_than_english,sd_lack_of_education,sd_date_scored | unpaired | - | 1: G33 |
| 11 | sd_individual_risk \| DateConversionRule \| sd_date_scored | unpaired | - | 1: G33 |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |

## databricks_notebook_details

- presence: compared; pair mode: key
- key columns used for pairing: DATABRICKS_NOTEBOOK_NAME
- rows: golden 6, agent 6, paired 6

### Golden rows

| golden row | key | status | agent row | source exports |
| --- | --- | --- | --- | --- |
| 2 | FileInvokeDQDeltaTable_V0.1 | paired | 1:2 | 1: G28 |
| 3 | DeltaInvokeDQStandardDeltaTable_V2 | paired | 1:3 | 1: G29 |
| 4 | FileInvokeDQDeltaTable_V0.1 | paired | 2:2 | 1: G30 |
| 5 | DeltaInvokeDQStandardDeltaTable_V2 | paired | 2:3 | 1: G31 |
| 6 | FileInvokeDQDeltaTable_V0.1 | paired | 3:2 | 1: G32 |
| 7 | DeltaInvokeDQStandardDeltaTable_V2 | paired | 3:3 | 1: G33 |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 1:2 | FileInvokeDQDeltaTable_V0.1 | paired | 2 |
| 1:3 | DeltaInvokeDQStandardDeltaTable_V2 | paired | 3 |
| 2:2 | FileInvokeDQDeltaTable_V0.1 | paired | 4 |
| 2:3 | DeltaInvokeDQStandardDeltaTable_V2 | paired | 5 |
| 3:2 | FileInvokeDQDeltaTable_V0.1 | paired | 6 |
| 3:3 | DeltaInvokeDQStandardDeltaTable_V2 | paired | 7 |

## stgdelta_stddelta_ingestion_det

- presence: compared; pair mode: key
- key columns used for pairing: OBJECT_NAME, TGT_TABLE_NAME
- rows: golden 3, agent 3, paired 3

### Golden rows

| golden row | key | status | agent row | source exports |
| --- | --- | --- | --- | --- |
| 2 | demographics_package \| sd_community_demographic_risk | paired | 1:2 | 1: G29 |
| 3 | analytics_package \| sd_community_risk | paired | 2:2 | 1: G31 |
| 4 | sd_ind_risk_data_package_G23_MI \| sd_individual_risk | paired | 3:2 | 1: G33 |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 1:2 | demographics_package \| sd_community_demographic_risk | paired | 2 |
| 2:2 | analytics_package \| sd_community_risk | paired | 3 |
| 3:2 | sd_ind_risk_data_package_G23_MI \| sd_individual_risk | paired | 4 |

## ADLS_FIXED_WIDTH_HANDLER

- presence: agent-only; pair mode: key
- key columns used for pairing: SEGMENT, TGT_TABLE
- rows: golden 0, agent 0, paired 0

No golden rows (sheet absent).

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
