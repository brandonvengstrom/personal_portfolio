-- You have been asked to support an investment firm by analyzing trends in high-growth companies. 
-- They are interested in understanding which industries are producing the highest valuations and the rate at which new high-value companies are emerging. 
-- Providing them with this information gives them a competitive insight as to industry trends and how they should structure their portfolio looking forward.

WITH TOTAL_UNI AS (
	SELECT 
		 INDUS.industry	   						  AS "industry"	
		,COUNT(*)		   					  AS "total_number_unicorn"
	FROM public.industries AS INDUS
		LEFT JOIN public.dates AS DATES
			ON INDUS.company_id = DATES.company_id
	WHERE 
		EXTRACT(YEAR FROM DATES.date_joined) IN (2019, 2020,2021)
	GROUP BY 
		INDUS.industry
	ORDER BY 
		"total_number_unicorn" DESC
	LIMIT 3
)

,

YEARLY_UNI AS (
	SELECT 
		 INDUS.industry                        				AS "industry"
		,EXTRACT(YEAR FROM DATES.date_joined)  				AS "year_joined"
		,COUNT(*)                              				AS "num_unicorns"
		,AVG(FUNDS.valuation)                  				AS "valuation"
	FROM public.industries AS INDUS
		LEFT JOIN public.dates AS DATES
			ON INDUS.company_id = DATES.company_id
		LEFT JOIN public.funding AS FUNDS
			ON INDUS.company_id = FUNDS.company_id
	WHERE 
		EXTRACT(YEAR FROM DATES.date_joined) IN (2019, 2020, 2021)
	GROUP BY 
		 "industry"
		,"year_joined"
)

SELECT 
	 TOTAL_UNI."industry"						       AS "industry"
	,YEARLY_UNI."year_joined"   					       AS "year"
	,YEARLY_UNI."num_unicorns"					       AS "num_unicorns"
	,ROUND(
		YEARLY_UNI."valuation"
		/ 1000000000
		,2
	)                           					       AS "average_valuation_billions"
FROM TOTAL_UNI
	LEFT JOIN YEARLY_UNI
		ON TOTAL_UNI."industry" = YEARLY_UNI."industry"
ORDER BY 
	 "year" DESC
	,"num_unicorns" DESC
