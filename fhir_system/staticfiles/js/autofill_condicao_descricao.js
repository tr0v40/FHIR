(function($){
    function wireRow($row){
      const $select = $row.find('select[id$="-condicao"]');
      const $textarea = $row.find('textarea[id$="-descricao"]');
      if(!$select.length || !$textarea.length) return;
  
      $select.on('change', function(){
        const id = $(this).val();
        if (!id || $textarea.val().trim().length) return; // não sobrescreve edição
        // base é a URL da página atual (add/change), sem a última barra
        const base = window.location.pathname.replace(/\/$/, '');
        const url  = base + '/condicao/' + id + '/descricao/';
        $.getJSON(url, function(data){
          if (data && typeof data.descricao === 'string'){
            $textarea.val(data.descricao);
          }
        });
      });
    }
  
    $(document).ready(function(){
      $('tr.form-row').each(function(){ wireRow($(this)); });
      $(document).on('formset:added', function(_e, $row){
        wireRow($row);
      });
    });
  })(django.jQuery);
  