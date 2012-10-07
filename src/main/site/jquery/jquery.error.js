(function($) {
    $.fn.errorStyle = function(element) {
        var id = this.attr('id');
        console.log(this.attr('id'));
        this.replaceWith(function(i,html){            
            var StyledError = '<div id="'+id+'" >';
            StyledError += "<div class=\"ui-state-error ui-corner-all\" style=\"padding: 0 .7em;\">";
            StyledError += "<p><span class=\"ui-icon ui-icon-alert\" style=\"float: left; margin-right: .3em;\">";
            StyledError += "</span><strong>NB : </strong>";
            StyledError += html;
            StyledError += "</p></div>";
            StyledError += '</div>';
            return StyledError;
        });
    }
})(jQuery);