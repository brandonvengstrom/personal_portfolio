 -- SPC is an established strategy that uses data to determine whether the process works well. Processes are only adjusted if measurements fall outside of an acceptable range. 
 -- This acceptable range is defined by an upper control limit (UCL) and a lower control limit (LCL), the formulas for which are:
 -- 
 -- ucl = avg_height + 3 * stddev_height / SQRT(5)$
 -- lcl = avg_height - 3 * stddev_height / SQRT(5)$
 --
 -- The UCL defines the highest acceptable height for the parts, while the LCL defines the lowest acceptable height for the parts. Ideally, parts should fall between the two limits.
 -- Using SQL window functions and nested queries, you'll analyze historical manufacturing data to define this acceptable range and identify any points in the process that fall outside of the range and therefore require adjustments. This will ensure a smooth running manufacturing process consistently making high-quality products.

SELECT 
	 "operator"                                        	 					AS "operator"
	,"row_number"	                                    					AS "row_number"
	,"height"                                           					AS "height"
	,"avg_height"	                                    					AS "avg_height"
	,"stddev_height"                                    					AS "stddev_height"
	,"avg_height" 
		+ 3 
		* ("stddev_height" / SQRT(5))										AS "ucl"
	,"avg_height" 
		- 3 
		* ("stddev_height" / SQRT(5))										AS "lcl"
	,CASE 
		WHEN "height" < "avg_height" - 3 * ("stddev_height" / SQRT(5))  
			THEN TRUE
		WHEN "height" > "avg_height" + 3 * ("stddev_height" / SQRT(5)) 
			THEN TRUE
		ELSE 
			FALSE
		END                                             					AS "alert"
FROM ( 
	SELECT 
		 operator															AS "operator"
		,ROW_NUMBER()
			OVER(
				PARTITION BY 
					operator
				ORDER BY item_no ASC 
			)																AS "row_number"
		,AVG("height")
			OVER(
				PARTITION BY 
					operator
				ORDER BY
					item_no ASC 
				ROWS BETWEEN 4 PRECEDING 
				AND CURRENT ROW
			)																AS "avg_height"
		,STDDEV("height")
			OVER(
				PARTITION BY 
					operator
				ORDER BY
					item_no ASC 
				ROWS BETWEEN 4 PRECEDING 
				AND CURRENT ROW
			)																AS "stddev_height"
		,height                             								AS "height"
	FROM manufacturing_parts
) AS SUB_MAN
WHERE 
	"row_number" > 4