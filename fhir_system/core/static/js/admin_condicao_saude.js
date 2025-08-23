(function($){
    function wireRow($row){
      const $select = $row.find('select[id$="-tipo_eficacia"]');
      const $textarea = $row.find('textarea[id$="-descricao"]');
      if(!$select.length || !$textarea.length) return;
  
      $select.on('change', function(){
        const id = $(this).val();
        // Não preenche se o campo descrição já foi editado
        if (!id || $textarea.val().trim().length) return;
  
        const base = window.location.pathname.replace(/\/$/, '');
        const url = base + '/tipoeficacia/' + id + '/descricao/';
  
        $.getJSON(url, function(data){
          if (data && typeof data.descricao === 'string'){
            $textarea.val(data.descricao);
          }
        });
      });
    }
  
    $(document).ready(function(){
      $('tr.form-row').each(function(){ wireRow($(this)); });
      $(document).on('formset:added', function(event, $row){
        wireRow($row);
      });
    });
  })(django.jQuery);
  