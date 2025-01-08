<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_i18n_Spanish.xsl                       -->
<!-- Content : PROTEUS default translations for Spanish       -->
<!-- Author  : Amador Durán Toro                              -->
<!--           José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/29                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->

<!-- ======================================================== -->
<!-- exclude-result-prefixes="proteus" must be set in all     -->
<!-- files to avoid xmlsn:proteus="." to appear in HTML tags. -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:proteus="http://proteus.us.es"
    xmlns:proteus-utils="http://proteus.us.es/utils"
    exclude-result-prefixes="proteus proteus-utils"
>

<!-- Same as default in REM 1.2.2 -->
<xsl:variable name="proteus:lang_action">Acción</xsl:variable>
<xsl:variable name="proteus:lang_address">Dirección</xsl:variable>
<xsl:variable name="proteus:lang_alternatives">Alternativas</xsl:variable>
<xsl:variable name="proteus:lang_analysis">Anólisis</xsl:variable>
<xsl:variable name="proteus:lang_attenders">Asistentes</xsl:variable>
<xsl:variable name="proteus:lang_attribute">Atributo</xsl:variable>
<xsl:variable name="proteus:lang_authors">Autores</xsl:variable>
<xsl:variable name="proteus:lang_average">Medio</xsl:variable>
<xsl:variable name="proteus:lang_category">Categoría</xsl:variable>
<xsl:variable name="proteus:lang_comments">Comentarios</xsl:variable>
<xsl:variable name="proteus:lang_components">Componentes</xsl:variable>
<xsl:variable name="proteus:lang_condition">Condición</xsl:variable>
<xsl:variable name="proteus:lang_constant_attribute">Atributo constante</xsl:variable>
<xsl:variable name="proteus:lang_constant_role">Rol constante</xsl:variable>
<xsl:variable name="proteus:lang_date">Fecha</xsl:variable>
<xsl:variable name="proteus:lang_definition">Definición</xsl:variable>
<xsl:variable name="proteus:lang_dependencies">Dependencias</xsl:variable>
<xsl:variable name="proteus:lang_derived_attribute">Atributo derivado</xsl:variable>
<xsl:variable name="proteus:lang_derived_role">Rol derivado</xsl:variable>
<xsl:variable name="proteus:lang_description">Descripción</xsl:variable>
<xsl:variable name="proteus:lang_directly_affected_objects">Afecta directamenta</xsl:variable>
<xsl:variable name="proteus:lang_disjoint_subtypes">Subtipos (disjuntos)</xsl:variable>
<xsl:variable name="proteus:lang_exception">Excepción</xsl:variable>
<xsl:variable name="proteus:lang_exceptions">Excepciones</xsl:variable>
<xsl:variable name="proteus:lang_expected_frequency">Frecuencia esperada</xsl:variable>
<xsl:variable name="proteus:lang_expression">Expresión</xsl:variable>
<xsl:variable name="proteus:lang_fax">Fax</xsl:variable>
<xsl:variable name="proteus:lang_figure">Figura</xsl:variable>
<xsl:variable name="proteus:lang_freelance">Freelance</xsl:variable>
<xsl:variable name="proteus:lang_if">Si</xsl:variable>
<xsl:variable name="proteus:lang_indirectly_affected_objects">Afecta indirectamente</xsl:variable>
<xsl:variable name="proteus:lang_invariant">Expresión de invariante</xsl:variable>
<xsl:variable name="proteus:lang_isCustomer">Es cliente</xsl:variable>
<xsl:variable name="proteus:lang_isDeveloper">Es desarrollador</xsl:variable>
<xsl:variable name="proteus:lang_isUser">Es usuario</xsl:variable>
<xsl:variable name="proteus:lang_importance">Importancia</xsl:variable>
<xsl:variable name="proteus:lang_initialValue">Valor inicial</xsl:variable>
<xsl:variable name="proteus:lang_lifetime">Tiempo de vida</xsl:variable>
<xsl:variable name="proteus:lang_maximum">Máximo</xsl:variable>
<xsl:variable name="proteus:lang_maximum_time">Tiempo máximo</xsl:variable>
<xsl:variable name="proteus:lang_meeting">Reunión</xsl:variable>
<xsl:variable name="proteus:lang_multiplicity">Multiplicidad</xsl:variable>
<xsl:variable name="proteus:lang_name">Nombre</xsl:variable>
<xsl:variable name="proteus:lang_no">No</xsl:variable>
<xsl:variable name="proteus:lang_none">Ninguno</xsl:variable>
<xsl:variable name="proteus:lang_OCL_condition">Condición (OCL)</xsl:variable>
<xsl:variable name="proteus:lang_OCL_expression">Expresión OCL</xsl:variable>
<xsl:variable name="proteus:lang_OCL_postconditions">Expresiones de postcondición (OCL)</xsl:variable>
<xsl:variable name="proteus:lang_OCL_preconditions">Expresiones de precondición (OCL)</xsl:variable>
<xsl:variable name="proteus:lang_ordinary_sequence">Secuencia normal</xsl:variable>
<xsl:variable name="proteus:lang_organization">Organización</xsl:variable>
<xsl:variable name="proteus:lang_overlapping_subtypes">Subtipos (solapados)</xsl:variable>
<xsl:variable name="proteus:lang_parameters">Parámetros</xsl:variable>
<xsl:variable name="proteus:lang_performance">Rendimiento</xsl:variable>
<xsl:variable name="proteus:lang_place">Lugar</xsl:variable>
<xsl:variable name="proteus:lang_possible_solution">Posible solución</xsl:variable>
<xsl:variable name="proteus:lang_postcondition">Postcondición</xsl:variable>
<xsl:variable name="proteus:lang_postconditions">Expresiones de postcondición</xsl:variable>
<xsl:variable name="proteus:lang_precondition">Precondición</xsl:variable>
<xsl:variable name="proteus:lang_preconditions">Expresiones de precondición</xsl:variable>
<xsl:variable name="proteus:lang_prepared_by">Preparado por:</xsl:variable>
<xsl:variable name="proteus:lang_prepared_for">Preparado para:</xsl:variable>
<xsl:variable name="proteus:lang_priority">Prioridad</xsl:variable>
<xsl:variable name="proteus:lang_project">Proyecto</xsl:variable>
<xsl:variable name="proteus:lang_related_objectives">Objetivos de los que depende</xsl:variable>
<xsl:variable name="proteus:lang_related_requirements">Requisitos de los que depende</xsl:variable>
<xsl:variable name="proteus:lang_result_type">Tipo del resultado</xsl:variable>
<xsl:variable name="proteus:lang_results">Resultados</xsl:variable>
<xsl:variable name="proteus:lang_role">Rol</xsl:variable>
<xsl:variable name="proteus:lang_simultaneous_ocurrences">Ocurrencias simultáneas</xsl:variable>
<xsl:variable name="proteus:lang_sources">Fuentes</xsl:variable>
<xsl:variable name="proteus:lang_specific_data">Datos específicos</xsl:variable>
<xsl:variable name="proteus:lang_stability">Estabilidad</xsl:variable>
<xsl:variable name="proteus:lang_stakeholder">Participante</xsl:variable>
<xsl:variable name="proteus:lang_status">Estado</xsl:variable>
<xsl:variable name="proteus:lang_step">Paso</xsl:variable>
<xsl:variable name="proteus:lang_subobjectives">Subobjetivos</xsl:variable>
<xsl:variable name="proteus:lang_subtypes">Subtipos</xsl:variable>
<xsl:variable name="proteus:lang_superclass">Supertipo</xsl:variable>
<xsl:variable name="proteus:lang_system">sistema</xsl:variable>
<xsl:variable name="proteus:lang_TBD">PD</xsl:variable>
<xsl:variable name="proteus:lang_telephone">Teléfono</xsl:variable>
<xsl:variable name="proteus:lang_then_this_use_case">a continuación este caso de uso</xsl:variable>
<xsl:variable name="proteus:lang_the">el</xsl:variable>
<xsl:variable name="proteus:lang_The">El</xsl:variable>
<xsl:variable name="proteus:lang_The_actor">El actor</xsl:variable>
<xsl:variable name="proteus:lang_the_actor">el actor</xsl:variable>
<xsl:variable name="proteus:lang_time">Hora</xsl:variable>
<xsl:variable name="proteus:lang_times_per">veces por</xsl:variable>
<xsl:variable name="proteus:lang_TOC">Índice</xsl:variable>
<xsl:variable name="proteus:lang_traceability_matrix">Matriz de trazabilidad</xsl:variable>
<xsl:variable name="proteus:lang_traceability_matrix_missing_class">No se puede visualizar la matriz de trazabilidad. Compruebe que hay al menos una clase seleccionada para las filas y columnas de la matriz.</xsl:variable>
<xsl:variable name="proteus:lang_traceability_matrix_missing_item">No se puede visualizar la matriz de trazabilidad. Compruebe que existe al menos un objeto de las clases selecionadas para las filas y columnas de la matriz.</xsl:variable>
<xsl:variable name="proteus:lang_type">Tipo</xsl:variable>
<xsl:variable name="proteus:lang_urgency">Urgencia</xsl:variable>
<xsl:variable name="proteus:lang_variable_attribute">Atributo variable</xsl:variable>
<xsl:variable name="proteus:lang_variable_role">Rol variable</xsl:variable>
<xsl:variable name="proteus:lang_version">Versión</xsl:variable>
<xsl:variable name="proteus:lang_yes">Sí</xsl:variable>
<xsl:variable name="proteus:lang_symlink_tooltip">Esta es una representación del objeto original. Modificar este objeto supone modificar el objeto original.</xsl:variable>
<xsl:variable name="proteus:lang_as_a">Como</xsl:variable>
<xsl:variable name="proteus:lang_i_want_to">Quiero</xsl:variable>
<xsl:variable name="proteus:lang_so_that">Para</xsl:variable>

<!-- new in PROTEUS -->
<xsl:variable name="proteus:lang_code_attributes">// atributos</xsl:variable>
<xsl:variable name="proteus:lang_code_components">// componentes</xsl:variable>
<xsl:variable name="proteus:lang_code_invariants">// invariantes</xsl:variable>
<xsl:variable name="proteus:lang_code_roles">// roles</xsl:variable>
<xsl:variable name="proteus:lang_code_preconditions">// precondiciones</xsl:variable>
<xsl:variable name="proteus:lang_code_postconditions">// postcondiciones</xsl:variable>
<xsl:variable name="proteus:lang_code_exception">exception</xsl:variable>
<xsl:variable name="proteus:lang_code_exceptions">// excepciones</xsl:variable>
<xsl:variable name="proteus:lang_web">Sitio web</xsl:variable>
<xsl:variable name="proteus:lang_empty_paragraph">Párrafo vacío</xsl:variable>
<xsl:variable name="proteus:lang_email">Correo-e</xsl:variable>

<xsl:variable name="proteus:lang">es</xsl:variable>
<xsl:variable name="proteus:lang_part">Parte</xsl:variable>
<xsl:variable name="proteus:lang_warnings">Avisos</xsl:variable>
<xsl:variable name="proteus:lang_abstract">abstracto</xsl:variable>
<xsl:variable name="proteus:lang_TBD_expanded">Por determinar</xsl:variable>

<xsl:variable name="proteus:lang_customer">Cliente</xsl:variable>
<xsl:variable name="proteus:lang_developer">Desarrollador</xsl:variable>
<xsl:variable name="proteus:lang_user">Usuario</xsl:variable>
<xsl:variable name="proteus:lang_strength">Fortaleza</xsl:variable>
<xsl:variable name="proteus:lang_weakness">Debilidad</xsl:variable>
<xsl:variable name="proteus:lang_diagram">Diagrama</xsl:variable>
<xsl:variable name="proteus:lang_participates_in">Participa en</xsl:variable>
<xsl:variable name="proteus:lang_critical">Crítica</xsl:variable>
<xsl:variable name="proteus:lang_high">Alta</xsl:variable>
<xsl:variable name="proteus:lang_medium">Media</xsl:variable>
<xsl:variable name="proteus:lang_low">Baja</xsl:variable>
<xsl:variable name="proteus:lang_optional">Opcional</xsl:variable>
<xsl:variable name="proteus:lang_draft">Borrador</xsl:variable>
<xsl:variable name="proteus:lang_awaiting_qa">Esperando verificación de calidad</xsl:variable>
<xsl:variable name="proteus:lang_awaiting_validation">Esperando validación</xsl:variable>
<xsl:variable name="proteus:lang_validated">Validado</xsl:variable>

<xsl:variable name="proteus:lang_child_requirements">Requisitos hijos</xsl:variable>
<xsl:variable name="proteus:lang_inherits_from">Hereda de</xsl:variable>
<xsl:variable name="proteus:lang_ordered">ordered</xsl:variable>

<xsl:variable name="proteus:lang_trace_type">Tipo de traza</xsl:variable>
<xsl:variable name="proteus:lang_trace_type_proteus_dependency">Depencia</xsl:variable>
<xsl:variable name="proteus:lang_trace_type_proteus_author">Autor</xsl:variable>
<xsl:variable name="proteus:lang_trace_type_proteus_affected">Elemento afectado</xsl:variable>
<xsl:variable name="proteus:lang_trace_type_proteus_information_source">Fuente de información</xsl:variable>
<xsl:variable name="proteus:lang_trace_type_proteus_works_for">Trabaja para</xsl:variable>

<xsl:variable name="proteus:lang_solution">Solución</xsl:variable>

<xsl:variable name="proteus:lang_defect_type_ambiguity">Ambigüedad</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_no_necessity">No necesidad</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_no_understanding">No comprensión</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_no_verificability">No verificabilidad</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_no_consistency">No consistencia</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_no_achievability">No alcanzabilidad</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_verbosity">Verborragia</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_design_dependence">Dependencia del diseño</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_redundancy">Redundancia</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_imprecision">Imprecisión</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_no_completeness">No completitud</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_no_priority">No prioridad</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_no_stability">No estabilidad</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_wrong_lod">Nivel de detalle incorrecto</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_no_traceability">No trazabilidad</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_wrong_org">Organización incorrecta</xsl:variable>
<xsl:variable name="proteus:lang_defect_type_other">Otro</xsl:variable>


<!-- ==================== -->
<!-- Patrones-L generales -->
<!-- ==================== -->

<xsl:variable name="proteus:lang_the_system_shall">El sistema deberá</xsl:variable>

<!-- ======================= -->
<!-- Patrones-L para actores -->
<!-- ======================= -->

<xsl:variable name="proteus:lang_this_actor_represents">Este actor representa</xsl:variable>

<!-- ========================================= -->
<!-- Patrones-L para requisitos de información -->
<!-- ========================================= -->

<xsl:variable name="proteus:lang_irq_lp_01">El sistema deberá almacenar la información correspondiente a</xsl:variable>
<xsl:variable name="proteus:lang_irq_lp_02">En concreto:</xsl:variable>

<!-- ========================================== -->
<!-- Patrones-L para requisitos de restricción  -->
<!-- ========================================== -->

<xsl:variable name="proteus:lang_crq_lp_01">El sistema deberá respetar la siguiente regla de negocio o restricción:</xsl:variable>

<!-- ============================ -->
<!-- Patrones-L para casos de uso -->
<!-- ============================= -->

<xsl:variable name="proteus:lang_uc_lp_01">El sistema deberá comportarse tal como se describe en el siguiente</xsl:variable>

<xsl:variable name="proteus:lang_uc_lp_02">caso de uso abstracto durante la realización de los siguientes casos de uso:</xsl:variable>

<xsl:variable name="proteus:lang_uc_lp_03">caso de uso cuando</xsl:variable>

<xsl:variable name="proteus:lang_uc_lp_04">o durante la realización de los siguientes casos de uso:</xsl:variable>

<xsl:variable name="proteus:lang_uc_lp_05">Se realiza el caso de uso</xsl:variable>

<xsl:variable name="proteus:lang_uc_lp_06">se realiza el caso de uso</xsl:variable>

<xsl:variable name="proteus:lang_uc_lp_07"></xsl:variable>

<!-- ================================ -->
<!-- Patrones-L para tipos de objetos -->
<!-- ================================ -->

<xsl:variable name="proteus:lang_ot_lp_01">Este tipo de objetos representa</xsl:variable>

<xsl:variable name="proteus:lang_ot_lp_02">Este tipo abstracto de objetos representa</xsl:variable>

<!-- =================================== -->
<!-- Patrones-L para tipos de asociación -->
<!-- =================================== -->

<xsl:variable name="proteus:lang_at_lp_01">Este tipo de asociación representa el hecho de que</xsl:variable>

<!-- ================================ -->
<!-- Patrones-L para tipos valor      -->
<!-- ================================ -->

<xsl:variable name="proteus:lang_vt_lp_01">Este tipo valor representa</xsl:variable>

<!-- ========================= -->
<!-- Patrones-L para atributos -->
<!-- ========================= -->

<xsl:variable name="proteus:lang_att_lp_01">Este atributo representa</xsl:variable>

<!-- ===================== -->
<!-- Patrones-L para roles -->
<!-- ===================== -->

<xsl:variable name="proteus:lang_role_lp_01">Este rol representa</xsl:variable>

</xsl:stylesheet>
