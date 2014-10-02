SET client_encoding TO 'UTF8';


CREATE OR REPLACE FUNCTION ag_get_barcode_md_animal (
    barcode_ IN text,
    user_data_ refcursor
)
 RETURNS refcursor AS $body$
BEGIN

open user_data_ for
select akb.barcode as sample_name,
        akb.barcode as ANONYMIZED_NAME, 
        akb.sample_date as collection_date, 
        'y' as "public",
        0 as depth,
        'American Gut Project ' || aas."type" || ' sample' as DESCRIPTION,
        akb.sample_time, 
        0 as altitude, 
        'y' as assigned_from_geo,
        'American Gut Project' as TITLE,
        akb.site_sampled,
        
        md5(md5(cast(aas.ag_login_id as varchar(100)) ||
                          aas.participant_name)) as host_subject_id,
        
        case akb.site_sampled
            when 'Stool' then '749906'
            when 'Mouth' then '1227552'
            when 'Nares' then '1115523'
            when 'Ears' then '410656'
            when 'Fur' then '1338477'
            when 'Skin' then '1338477'
            when 'Please select...' then 'unknown'
            else akb.site_sampled
        end as TAXON_ID,
        case aas."type"
            when 'Dog' then '9615'
            when 'Cat' then '9685'
            when 'Bird' then '8782'
            when 'Fish' then '7777'
            when 'Small Mammal' then '40674'
            when 'Large Mammal' then '40674'
            when 'Reptile' then '8459'
            when 'Amphibian' then '8292'
            when 'Other' then '33208'
            else aas."type"
        end as host_taxid,
        case akb.site_sampled
            when 'Stool' then 'gut metagenome'
            when 'Mouth' then 'oral metagenome'
            when 'Nares' then 'upper respiratory metagenome'
            when 'Ears' then 'organismal metagenome'
            when 'Fur' then 'skin metagenome'
            when 'Skin' then 'skin metagenome'
            when 'Please select...' then 'unknown'
            else akb.site_sampled
        end as common_name,        
        aas."type" as host_common_name,
        case akb.site_sampled
            when 'Stool' then 'UBERON:feces'
            when 'Mouth' then 'UBERON:oral cavity'
            when 'Nares' then 'UBERON:nose'
            when 'Ears' then 'UBERON:ear'
            when 'Fur' then 'UBERON:fur'
            when 'Skin' then 'UBERON:skin'
            when 'Please select...' then 'unknown'
            else akb.site_sampled
        end as body_habitat, 
        case akb.site_sampled
            when 'Stool' then 'UBERON:feces'
            when 'Mouth' then 'UBERON:tongue'
            when 'Nares' then 'UBERON:nostril'
            when 'Ears' then 'UBERON:skin'
            when 'Fur' then 'UBERON:fur'
            when 'Skin' then 'UBERON:skin'
            when 'Please select...' then 'unknown'
            else akb.site_sampled
        end as body_site, 
        case akb.site_sampled
            when 'Stool' then 'UBERON:feces'
            when 'Mouth' then 'UBERON:saliva'
            when 'Nares' then 'UBERON:mucus'
            when 'Ears' then 'UBERON:cerumen'
            when 'Fur' then 'UBERON:sebum'
            when 'Skin' then 'UBERON:sebum'
            when 'Please select...' then 'unknown'
            else akb.site_sampled
        end as body_product, 
        case akb.site_sampled
            when 'Stool' then 'ENVO:urban biome'
            when 'Mouth' then 'ENVO:urban biome'
            when 'Nares' then 'ENVO:urban biome'
            when 'Ears' then 'ENVO:urban biome'
            when 'Fur' then 'ENVO:urban biome'
            when 'Skin' then 'ENVO:urban biome'
            when 'Please select...' then 'unknown'
            else akb.site_sampled
        end as env_biome, 
        case akb.site_sampled
            when 'Stool' then 'ENVO:animal-associated habitat'
            when 'Mouth' then 'ENVO:animal-associated habitat'
            when 'Nares' then 'ENVO:animal-associated habitat'
            when 'Ears' then 'ENVO:animal-associated habitat'
            when 'Fur' then 'ENVO:animal-associated habitat'
            when 'Skin' then 'ENVO:animal-associated habitat'
            when 'Please select...' then 'unknown'
            else akb.site_sampled
        end as env_feature, 
        case akb.site_sampled
            when 'Stool' then 'ENVO:feces'
            when 'Mouth' then 'ENVO:saliva'
            when 'Nares' then 'ENVO:mucus'
            when 'Ears' then 'ENVO:cerumen'
            when 'Fur' then 'ENVO:sebum'
            when 'Skin' then 'ENVO:mucus'
            when 'Please select...' then 'unknown'
            else akb.site_sampled
        end as env_matter,
        case
            when coalesce(city::text, '') = '' then 'unknown'
            else lower(city)
        end as city, 
        case
            when coalesce(state::text, '') = '' then 'unknown'
            else upper(state)
        end as state,
        case 
            when coalesce(zip::text, '') = '' then 'unknown'
            else zip
        end as zip,
        case 
            when lower(country) is null then 'unknown'
            when lower(country) = 'united states' then 'GAZ:United States of America'
            when lower(country) = 'united states of america' then 'GAZ:United States of America'
            when lower(country) = 'us' then 'GAZ:United States of America'
            when lower(country) = 'usa' then 'GAZ:United States of America'
            when lower(country) = 'u.s.a' then 'GAZ:United States of America'
            when lower(country) = 'u.s.' then 'GAZ:United States of America'
            when lower(country) = 'canada' then 'GAZ:Canada'
            when lower(country) = 'canadian' then 'GAZ:Canada'
            when lower(country) = 'ca' then 'GAZ:Canada'
            when lower(country) = 'australia' then 'GAZ:Australia'
            when lower(country) = 'au' then 'GAZ:Australia'
            when lower(country) = 'united kingdom' then 'GAZ:United Kingdom'
            when lower(country) = 'belgium' then 'GAZ:Belgium'
            when lower(country) = 'gb' then 'GAZ:Great Britain'
            when lower(country) = 'korea, republic of' then 'GAZ:South Korea'
            when lower(country) = 'nl' then 'GAZ:Netherlands'
            when lower(country) = 'netherlands' then 'GAZ:Netherlands'
            when lower(country) = 'spain' then 'GAZ:Spain'
            when lower(country) = 'es' then 'GAZ:Spain'
            when lower(country) = 'norway' then 'GAZ:Norway'
            when lower(country) = 'germany' then 'GAZ:Germany'
            when lower(country) = 'de' then 'GAZ:Germany'
            when lower(country) = 'china' then 'GAZ:China'
            when lower(country) = 'singapore' then 'GAZ:Singapore'
            when lower(country) = 'new zealand' then 'GAZ:New Zealand'
            when lower(country) = 'france' then 'GAZ:France'
            when lower(country) = 'fr' then 'GAZ:France'
            when lower(country) = 'ch' then 'GAZ:Switzerland'
            when lower(country) = 'switzerland' then 'GAZ:Switzerland'
            when lower(country) = 'denmark' then 'GAZ:Denmark'
            when lower(country) = 'scotland' then 'GAZ:Scotland'
            when lower(country) = 'united arab emirates' then 'GAZ:United Arab Emirates'
            when lower(country) = 'ireland' then 'GAZ:Ireland'
            else 'unknown'
        end as country,
        case
            when coalesce(al.latitude::text, '') = '' then 'unknown'
            else cast(al.latitude as varchar(100))
        end as latitude, 
        case
            when coalesce(al.longitude::text, '') = '' then 'unknown'
            else cast(al.longitude as varchar(100))
        end as longitude, 
        case
            when coalesce(al.elevation::text, '') = '' then 'unknown'
            else cast(al.elevation as varchar(100))
        end as elevation, 
        'years' as age_unit,
        aas.age,
        case
            when coalesce(GENDER::text, '') = '' then 'unknown'
            else lower(REPLACE(REPLACE(REPLACE(cast (GENDER as text), CHR(10), ''), CHR(13), ''), CHR(9), ''))
        end as sex,
        case
            when coalesce(aas.coprophage::text, '') = '' then 'unknown'
            else aas.coprophage
        end as coprophage,
        case
            when coalesce(aas.diet::text, '') = '' then 'unknown'
            else aas.diet
        end as diet,
        case
            when coalesce(aas.food_source_human::text, '') = '' then 'unknown'
            when aas.food_source_human = 'on' then 'yes'
        end as eats_human_food,
        case
            when coalesce(aas.food_source_store::text, '') = '' then 'unknown'
            when aas.food_source_store = 'on' then 'yes'
        end as eats_store_food,
        case
            when coalesce(aas.food_source_wild::text, '') = '' then 'unknown'
            when aas.food_source_wild = 'on' then 'yes'
        end as eats_wild_food,
        case
            when coalesce(aas.food_type::text, '') = '' then 'unknown'
            else aas.food_type
        end as food_type,
        case
            when coalesce(aas.grain_free_food::text, '') = '' then 'unknown'
            when aas.grain_free_food = 'on' then 'yes'
        end as eats_grain_free_food,
        case
            when coalesce(aas.organic_food::text, '') = '' then 'unknown'
            when aas.organic_food = 'on' then 'yes'
        end as eats_organic_food,
        case
            when coalesce(aas.living_status::text, '') = '' then 'unknown'
            else aas.living_status
        end as living_status,
        case
            when coalesce(aas.origin::text, '') = '' then 'unknown'
            else aas.origin
        end as origin,
        case
            when coalesce(aas.outside_time::text, '') = '' then 'unknown'
            when aas.outside_time = 'none' then '0'
            else aas.outside_time
        end as outside_time,
        case
            when coalesce(aas.setting::text, '') = '' then 'unknown'
            else aas.setting
        end as setting,
        case
            when coalesce(aas.toilet::text, '') = '' then 'uknown'
            else aas.toilet
        end as toile_water_access,
        case
            when coalesce(aas.weight::text, '') = '' then 'unknown'
            else aas.weight
        end as weight_class,

        -- multiples
        case
            when 
            (
                SELECT  string_agg(item_value, ',' order by item_name)
                from    ag_survey_multiples
                where   ag_login_id = al.ag_login_id
                        and participant_name = akb.participant_name
                        and item_name like 'human/_%/_sex' escape '/'
            ) is null then 'unknown'
            else 
            (
                SELECT  string_agg(item_value, ',' order by item_name)
                from    ag_survey_multiples
                where   ag_login_id = al.ag_login_id
                        and participant_name = akb.participant_name
                        and item_name like 'human/_%/_sex' escape '/'
            )
        end as human_sexes,

        case
            when 
            (
                SELECT  string_agg(item_value, ',' order by item_name)
                from    ag_survey_multiples
                where   ag_login_id = al.ag_login_id
                        and participant_name = akb.participant_name
                        and item_name like 'human/_%/_age' escape '/'
            ) is null then 'unknown'
            else 
            (
                SELECT  string_agg(item_value, ',' order by item_name)
                from    ag_survey_multiples
                where   ag_login_id = al.ag_login_id
                        and participant_name = akb.participant_name
                        and item_name like 'human/_%/_age' escape '/'
            )
        end as human_ages,

        case
            when 
            (
                SELECT  string_agg(item_value, ',' order by item_name)
                from    ag_survey_multiples
                where   ag_login_id = al.ag_login_id
                        and participant_name = akb.participant_name
                        and item_name like 'pet/_%' escape '/'
            ) is null then 'unknown'
            else 
            (
                SELECT  string_agg(item_value, ',' order by item_name)
                from    ag_survey_multiples
                where   ag_login_id = al.ag_login_id
                        and participant_name = akb.participant_name
                        and item_name like 'pet/_%' escape '/'
            )
        end as pets_cohoused
        
from    ag_login al
        inner join ag_kit ak
        on al.ag_login_id = ak.ag_login_id
        inner join ag_kit_barcodes akb
        on ak.ag_kit_id = akb.ag_kit_id
        inner join ag_animal_survey aas
        on al.ag_login_id = aas.ag_login_id
where   akb.participant_name = aas.participant_name
        and (akb.site_sampled IS NOT NULL AND akb.site_sampled::text <> '')
        and akb.site_sampled != 'Please Select...'
        and (akb.sample_date IS NOT NULL AND akb.sample_date::text <> '')
        and akb.barcode = barcode_;
return user_data_;
end;
/*
begin;
select ag_get_barcode_md_animal('000013395', 'a');
fetch all in a;
commit;
*/

$body$
LANGUAGE PLPGSQL;




