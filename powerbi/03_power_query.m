// LandslideWatch - Power Query (M). Paste each block into Home > Transform data > New Source > Blank Query > Advanced Editor.
// Change DataFolder once, in the first query (parameter), and every other query follows it.

// ===== Query: DataFolder (make this a Parameter: Manage Parameters > New, Type Text) =====
"C:\Users\Rehan\Documents\landslide-powerbi\data\" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]

// ===== Query: fact_landslides =====
let
    Source   = Csv.Document(File.Contents(DataFolder & "fact_landslides.csv"), [Delimiter = ",", Columns = 60, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // "en-US" culture matters: it stops an Indian/UK regional setting from reading dates or decimals the wrong way round
    Typed    = Table.TransformColumnTypes(Promoted, {
        {"event_id", Int64.Type},
        {"event_date", type date},
        {"event_datetime", type datetime},
        {"year", Int64.Type},
        {"quarter", type text},
        {"month_num", Int64.Type},
        {"month_name", type text},
        {"year_month", type date},
        {"day_of_week", type text},
        {"season", type text},
        {"hemisphere", type text},
        {"event_title", type text},
        {"location_description", type text},
        {"event_description_short", type text},
        {"source_name", type text},
        {"source_group", type text},
        {"source_link", type text},
        {"country_name", type text},
        {"country_code", type text},
        {"country_source", type text},
        {"continent", type text},
        {"subregion", type text},
        {"is_india_flag", Int64.Type},
        {"admin_division", type text},
        {"admin_source", type text},
        {"latitude", type number},
        {"longitude", type number},
        {"grid_1deg", type text},
        {"grid_lat", type number},
        {"grid_lon", type number},
        {"location_accuracy", type text},
        {"accuracy_km", Int64.Type},
        {"high_precision_flag", Int64.Type},
        {"category", type text},
        {"category_group", type text},
        {"trigger", type text},
        {"trigger_group", type text},
        {"size", type text},
        {"size_rank", Int64.Type},
        {"setting", type text},
        {"setting_group", type text},
        {"storm_name", type text},
        {"fatality_count", Int64.Type},
        {"fatality_reported_flag", Int64.Type},
        {"fatal_event_flag", Int64.Type},
        {"fatality_band", type text},
        {"fatality_band_sort", Int64.Type},
        {"injury_count", Int64.Type},
        {"injury_reported_flag", Int64.Type},
        {"admin_population", Int64.Type},
        {"population_known_flag", Int64.Type},
        {"nearest_place", type text},
        {"nearest_place_km", type number},
        {"submitted_date", type date},
        {"report_lag_days", Int64.Type},
        {"lag_negative_flag", Int64.Type},
        {"is_test_import_flag", Int64.Type},
        {"possible_duplicate_flag", Int64.Type},
        {"complete_year_flag", Int64.Type},
        {"core_period_flag", Int64.Type}
    }, "en-US")
in
    Typed

// ===== Query: dim_date =====
let
    Source   = Csv.Document(File.Contents(DataFolder & "dim_date.csv"), [Delimiter = ",", Columns = 9, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // "en-US" culture matters: it stops an Indian/UK regional setting from reading dates or decimals the wrong way round
    Typed    = Table.TransformColumnTypes(Promoted, {
        {"date", type date},
        {"year", Int64.Type},
        {"quarter", type text},
        {"month_num", Int64.Type},
        {"month_name", type text},
        {"year_month", type date},
        {"day_of_week", type text},
        {"day_of_week_num", Int64.Type},
        {"week_of_year", Int64.Type}
    }, "en-US")
in
    Typed

// ===== Query: dim_country =====
let
    Source   = Csv.Document(File.Contents(DataFolder & "dim_country.csv"), [Delimiter = ",", Columns = 5, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // "en-US" culture matters: it stops an Indian/UK regional setting from reading dates or decimals the wrong way round
    Typed    = Table.TransformColumnTypes(Promoted, {
        {"country_name", type text},
        {"country_code", type text},
        {"continent", type text},
        {"subregion", type text},
        {"is_india_flag", Int64.Type}
    }, "en-US")
in
    Typed

// ===== Query: dim_trigger =====
let
    Source   = Csv.Document(File.Contents(DataFolder & "dim_trigger.csv"), [Delimiter = ",", Columns = 2, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // "en-US" culture matters: it stops an Indian/UK regional setting from reading dates or decimals the wrong way round
    Typed    = Table.TransformColumnTypes(Promoted, {
        {"trigger", type text},
        {"trigger_group", type text}
    }, "en-US")
in
    Typed

// ===== Query: dim_size =====
let
    Source   = Csv.Document(File.Contents(DataFolder & "dim_size.csv"), [Delimiter = ",", Columns = 2, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // "en-US" culture matters: it stops an Indian/UK regional setting from reading dates or decimals the wrong way round
    Typed    = Table.TransformColumnTypes(Promoted, {
        {"size", type text},
        {"size_rank", Int64.Type}
    }, "en-US")
in
    Typed

// ===== Query: dim_category =====
let
    Source   = Csv.Document(File.Contents(DataFolder & "dim_category.csv"), [Delimiter = ",", Columns = 2, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // "en-US" culture matters: it stops an Indian/UK regional setting from reading dates or decimals the wrong way round
    Typed    = Table.TransformColumnTypes(Promoted, {
        {"category", type text},
        {"category_group", type text}
    }, "en-US")
in
    Typed

// ===== Query: dim_setting =====
let
    Source   = Csv.Document(File.Contents(DataFolder & "dim_setting.csv"), [Delimiter = ",", Columns = 2, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // "en-US" culture matters: it stops an Indian/UK regional setting from reading dates or decimals the wrong way round
    Typed    = Table.TransformColumnTypes(Promoted, {
        {"setting", type text},
        {"setting_group", type text}
    }, "en-US")
in
    Typed

// ===== Query: data_quality_log =====
let
    Source   = Csv.Document(File.Contents(DataFolder & "data_quality_log.csv"), [Delimiter = ",", Columns = 2, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // "en-US" culture matters: it stops an Indian/UK regional setting from reading dates or decimals the wrong way round
    Typed    = Table.TransformColumnTypes(Promoted, {
        {"step", type text},
        {"detail", type text}
    }, "en-US")
in
    Typed
