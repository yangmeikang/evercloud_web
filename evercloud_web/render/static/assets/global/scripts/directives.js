/***
GLobal Directives
***/

// Route State Load Spinner(used on page or content load)
angular.module('cloud.directives', [])

.directive('ngSpinnerBar', ['$rootScope',
    function($rootScope) {
        return {
            link: function(scope, element, attrs) {
                // by defult hide the spinner bar
                element.addClass('hide'); // hide spinner bar by default

                // display the spinner bar whenever the route changes(the content part started loading)
                $rootScope.$on('$stateChangeStart', function() {
                    element.removeClass('hide'); // show spinner bar
                });

                // hide the spinner bar on rounte change success(after the content loaded)
                $rootScope.$on('$stateChangeSuccess', function() {
                    element.addClass('hide'); // hide spinner bar
                    $('body').removeClass('page-on-load'); // remove page loading indicator
                    Layout.setSidebarMenuActiveLink('match'); // activate selected link in the sidebar menu
                   
                    // auto scorll to page top
                    setTimeout(function () {
                        Metronic.scrollTop(); // scroll to the top on content load
                    }, $rootScope.settings.layout.pageAutoScrollOnLoad);     
                });

                // handle errors
                $rootScope.$on('$stateNotFound', function() {
                    element.addClass('hide'); // hide spinner bar
                });

                // handle errors
                $rootScope.$on('$stateChangeError', function() {
                    element.addClass('hide'); // hide spinner bar
                });
            }
        };
    }
])

// Handle global LINK click
.directive('a', function() {
    return {
        restrict: 'E',
        link: function(scope, elem, attrs) {
            if (attrs.ngClick || attrs.href === '' || attrs.href === '#') {
                elem.on('click', function(e) {
                    e.preventDefault(); // prevent link click for above criteria
                });
            }
        }
    };
})

// Handle Dropdown Hover Plugin Integration
.directive('dropdownMenuHover', function () {
  return {
    link: function (scope, elem) {
      elem.dropdownHover();
    }
  };  
})

.directive('napAfterClick', function($timeout) {
    return {
        restrict: 'A',
        link: function(scope, elem, attrs) {

            var duration = parseInt(attrs.napAfterClick);

            if(isNaN(duration)){
                duration = 2;
            }

            duration *= 1000;

            elem.on('click', function(){
                elem.addClass('disabled');
                $timeout(function(){
                    elem.removeClass('disabled');
                }, duration);
            });
        }
    };
})

.directive('eonDatePicker', function($timeout, DatePicker){
    return {
        link: function(scope, element, attrs) {
            $timeout(function() {
                DatePicker.initDatePickers(element);
            });
        }
    };
})

.directive('eonHelp', function(){
    return {
        restrict: 'E',
        replace: true,
        template: "<a><i class=\"fa fa-question-circle\"></i></a>"
    }
});
