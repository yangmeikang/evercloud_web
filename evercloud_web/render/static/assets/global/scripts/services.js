/**
 * User: bluven
 * Date: 2015-7-13 2:36
 */

angular.module('cloud.services', [])

.factory('settings', ['$rootScope', function ($rootScope) {
    var settings = {
        layout: {
            pageSidebarClosed: false, // sidebar menu state
            pageBodySolid: true, // solid body color state
            pageAutoScrollOnLoad: 1000 // auto scroll to top on page load
        },
        layoutImgPath: Metronic.getAssetsPath() + 'admin/layout/img/',
        layoutCssPath: Metronic.getAssetsPath() + 'admin/layout/css/'
    };
    $rootScope.settings = settings;

    return settings;
}])

.factory("AuthInterceptor", [function($q){
    return {
        'responseError': function(rejection){
            if (rejection.status == 403 || rejection.status == 401) {
                window.location.href = "/login/";
                return $q.reject(rejection);
            }
            return rejection;
        }
    }
}])

.factory("CommonHttpService", function($http, $q){
    return {
        'get': function(api_url){
            var defer = $q.defer();
            $http({
                method: 'GET',
                url: api_url
            }).success(function(data, status, headers, config){
                defer.resolve(data);
            }).error(function(data, status, headers, config){
                defer.reject(data);
            });
            return defer.promise;
        },
        'post': function(api_url, post_data){
            var defer = $q.defer();
            $http({
                method: 'POST',
                url: api_url,
                data: $.param(post_data)
            }).success(function(data, status, headers,config){
                defer.resolve(data);
            }).error(function(data, status, headers, config){
                defer.reject(data);
            });
            return defer.promise;
        }
    };
})

.factory('ResourceTool', function(){
  return {
    'copy_only_data': function(data){

      var result = {};

      for(var attr in data){
        if(attr.startsWith('$') || attr == 'toJSON'){
          continue;
        }
        result[attr] = data[attr];
      }

      return result;
    }
  }
})

.factory('ToastrService', function () {
    toastr.options = {
        "closeButton": true,
        "debug": false,
        "positionClass": "toast-top-right",
        "onclick": null,
        "showDuration": "1000",
        "hideDuration": "1000",
        "timeOut": "5000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    };
    return {
        success: function (message, title) {
            toastr.success(message, title);
        },
        warning: function (message, title) {
            toastr.warning(message, title);
        },
        error: function (message, title) {
            toastr.error(message, title);
        }
    };
})

.factory('ValidationTool', function(){

    var defaultConfig = {
        onkeyup: false,
        doNotHideMessage: true,
        errorElement: 'span',
        errorClass: 'help-block help-block-error',
        focusInvalid: false,
        errorPlacement: function (error, element) {
            element.parent().append(error);
        },

        highlight: function (element) {
            $(element).closest('.form-group').removeClass('has-success').addClass('has-error');
        },

        unhighlight: function (element) {
            $(element).closest('.form-group').removeClass('has-error').addClass('has-success');
        }
    };

    return {
        init: function(selector, config){

            config = config || {};

            for(var attr in defaultConfig){
                if(config[attr] === undefined){
                    config[attr] = defaultConfig[attr];
                }
            }
            $(selector).validate(config);

            return $(selector);
        },
        addValidator: $.validator.addMethod
    }
})

.factory('CheckboxGroup', function(){

    var init = function(objects, flagName){

        flagName = flagName || 'checked';

        var groupChecker = {
            objects: objects,
            toggleAll: function(){
                var self = this;
                angular.forEach(self.objects, function(obj){
                    obj[flagName] = self[flagName];
                });
            },
            noneChecked: function(){
                var count = 0;

                angular.forEach(this.objects, function(obj){
                    if(obj[flagName]){
                        count += 1;
                    }
                });

                return count == 0;
            },
            syncObjects: function(objects){
                this.objects = objects;
            },
            uncheck: function(){
                this[flagName] = false;
                this.toggleAll();
            },
            forEachChecked: function(func){
                angular.forEach(this.objects, function(obj){
                    if(obj[flagName]){
                       func(obj);
                    }
                });
            },
            checkedObjects: function(){
                var results = [];
                this.forEachChecked(function(obj){
                    results.push(obj);
                });
                return results;
            }
        };

        groupChecker[flagName] = false;

        return groupChecker;
    };

    return {init: init};

})

/* Init date pickers, more functions come later. */
.factory('DatePicker', function (){

    var initDatePickers = function(selector){

        selector = selector || '.date-picker';
        if (jQuery().datepicker) {
            $(selector).datepicker({
                rtl: Metronic.isRTL(),
                orientation: "left",
                format: 'yyyy-mm-dd',
                autoclose: true
            });
        }
    };

    var initDateTimePickers = function(config){

        config = config || {};

        var defaultConfig = {
            autoclose: true,
            isRTL: Metronic.isRTL(),
            pickerPosition: (Metronic.isRTL() ? "bottom-right" : "bottom-left"),
            format: "yyyy-mm-dd hh:ii",
            autoclose: true,
            todayBtn: true,
            minuteStep: 10
        };

        angular.extend(defaultConfig, config);

        $(".form_datetime").datetimepicker(defaultConfig);
    };

    return {
        initDatePickers: initDatePickers,
        initDateTimePickers: initDateTimePickers
    }
})

.factory('ngTableHelper', function(){

        var countPages = function(params, total){

            params.total(total);

            var pageNum = Math.ceil(total / params.count());

            if(pageNum == 0){
                pageNum = 1;
            }

            if(pageNum < params.page()){
                params.page(pageNum);
            }
        };

        var paginate = function(data, $defer, params){

            if(!angular.isArray(data)){
               return data;
            }

            countPages(params, data.length);

            var start = (params.page() - 1) * params.count(),
                end = params.page() * params.count(),
                partial = data.slice(start, end);

            $defer.resolve(partial);

            return partial;
        };

        return {
            countPages: countPages,
            paginate: paginate
        };
    })

    .controller('ChangePasswordController',
        function($scope, $modalInstance, $i18next, $window, $timeout, ngTableParams,
             CommonHttpService, ValidationTool, ToastrService){

                var form = null;

                $scope.params = {old_password: '', new_password: '', confirm_password: ''};

                $scope.cancel = $modalInstance.dismiss;

                $modalInstance.rendered.then(function(){
                    form = ValidationTool.init('#passwordForm');
                });

                $scope.changePassword = function(){

                    if(!form.valid()){
                        return;
                    }

                    CommonHttpService.post('/api/users/change-password/', $scope.params).then(function(result){
                        if(result.success){
                            ToastrService.success(result.msg, $i18next("success"));
                            $modalInstance.close();
                            $timeout(function(){
                                window.location.href = "/login/";
                            }, 5000);
                        } else {
                            ToastrService.error(result.msg, $i18next("op_failed"));
                        }
                    });
                }
        }
    )

    .controller('ProfileController',
        function($scope, $modalInstance, $i18next, $window, $timeout,
             CommonHttpService, ValidationTool, ToastrService){

                var form = null;

                $scope.user = angular.copy($scope.current_user);
                $scope.cancel = $modalInstance.dismiss;

                $modalInstance.rendered.then(function(){
                    form = ValidationTool.init('#profileForm');
                });

                $scope.save = function(){

                    if(!form.valid()){
                        return;
                    }

                    CommonHttpService.post('/api/users/change-profile/', $scope.user).then(function(result){
                        if(result.success){
                            ToastrService.success(result.msg, $i18next("success"));
                            $scope.current_user.mobile = $scope.user.mobile;
                            $scope.current_user.email = $scope.user.email;
                            $modalInstance.close();
                        } else {
                            ToastrService.error(result.msg, $i18next("op_failed"));
                        }
                    });
                }
        }
    )
    .factory('UserProfileService', ['$modal', function($modal){

        var  openProfileModal = function(){
            $modal.open({
                templateUrl: '/static/assets/global/views/profile.html',
                backdrop: "static",
                controller: 'ProfileController',
                size: 'lg'
            });
        };

        var openPasswordModal = function(){
            $modal.open({
                templateUrl: '/static/assets/global/views/change-password.html',
                controller: 'ChangePasswordController',
                backdrop: "static",
                size: 'lg'
            });
        };

        return {openProfileModal: openProfileModal, openPasswordModal: openPasswordModal};
    }])
    .factory('PriceTool', function($interpolate, lodash){

        var diffFormat = $interpolate("{[{ price }]} + (n - {[{ flavor_start -1 }]}) * {[{ diff_price }]}");

        var hourPriceFormat = function(rule){
            return diffFormat({
                price: rule.hour_price,
                diff_price: rule.hour_diff_price,
                flavor_start: rule.resource_flavor_start
            });
        };

        var monthPriceFormat = function(rule){
            return diffFormat({
                price: rule.month_price,
                diff_price: rule.month_diff_price,
                flavor_start: rule.resource_flavor_start
            });
        };

        var getPrice = function(prices, flavor, payType){

            prices = lodash.filter(prices, function(price){
                return flavor >= price.resource_flavor_start;
            });

            var price = null;
            if(prices.length > 0){
                price = prices.pop();
            } else {
                price = {hour_price: 0, month_price: 0, price_type: 'normal'}
            }

            if(payType == 'hour'){
                price.price = price.hour_price;
                price.diff_price = price.hour_diff_price;
            } else {
                price.price = price.month_price;
                price.diff_price = price.month_diff_price;
            }

            if(price.price_type != 'diff'){
                return price.price;
            } else {
                return price.price + (flavor - price.resource_flavor_start + 1) * price.diff_price;
            }
        };

        return {
            hourPriceFormat: hourPriceFormat,
            monthPriceFormat: monthPriceFormat,
            getPrice: getPrice
        };
    })
    .filter("humanizeDiskSize", function(){
        return function(size){
            var units = ['MB', 'GB', 'TB', 'PB'];

            for(var i = 0; i < units.length; i++){
                if(size < 1000){
                    return "" + size + units[i];
                } else {
                    size /= 1000;
                }
            }
        };
    });

